#!/usr/bin/env node
/**
 * Scrapes live arrival/departure rows from the official CSMIA Mumbai flight status page
 * and writes `data/mock/flights.json` in the backend Flight schema shape.
 *
 * Requires: npm install (root) && npx playwright install chromium
 */
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, '..');
const OUT = path.join(REPO, 'data', 'mock', 'flights.json');
const SOURCE_URL = 'https://csmia-mumbai.adaniairports.com/en/flight-status';

async function collectFromDom(page, tableBodySelector, legType) {
  return page.evaluate(
    ({ sel, leg }) => {
      const root = document.querySelector(sel);
      if (!root) return [];
      const rows = [...root.querySelectorAll('.flightListRow')];
      return rows
        .map((row) => {
          const cols = [...row.querySelectorAll(':scope > .flightListCol')];
          if (cols.length < 6) return null;

          const timeCol = cols[0];
          const reg = timeCol.querySelector('.regularTime');
          let scheduled = '';
          let estimated = '';
          if (reg) {
            scheduled = reg.textContent.trim();
            estimated = timeCol.textContent.replace(reg.textContent, '').replace(/\s+/g, ' ').trim();
          } else {
            scheduled = timeCol.textContent.replace(/\s+/g, ' ').trim();
          }

          const labelEl = cols[1].querySelector('label');
          const airline = labelEl ? labelEl.textContent.trim() : '';
          const h6 = cols[1].querySelector('h6');
          let route = '';
          if (h6) {
            route = h6.textContent
              .replace(labelEl ? labelEl.textContent : '', '')
              .replace(/\s+/g, ' ')
              .trim();
          }

          const flightNo = cols[2].textContent.replace(/Flight No/gi, '').replace(/\s+/g, ' ').trim();
          const terminal = cols[3].textContent.replace(/Terminal/gi, '').replace(/\s+/g, ' ').trim();
          const extraCol = cols[4].textContent
            .replace(/Baggage Belt/gi, '')
            .replace(/Gate/gi, '')
            .replace(/\s+/g, ' ')
            .trim();
          const statusBtn = cols[5].querySelector('button.statusButton, button');
          const status = statusBtn
            ? statusBtn.textContent.replace(/\s+/g, ' ').trim()
            : cols[5].textContent.replace(/\s+/g, ' ').trim();

          if (!flightNo) return null;

          const timings = {
            scheduled,
            ...(estimated ? { estimated } : {}),
            ...(route ? { route } : {}),
            ist_note: 'IST (GMT+5:30)',
          };

          const base = flightNo.replace(/\s+/g, '_').replace(/[^A-Za-z0-9_]/g, '');
          const fid = `${base}_${leg === 'departure' ? 'DEP' : 'ARR'}`.toUpperCase();

          if (leg === 'arrival') {
            timings.baggage_belt = extraCol || '';
            return {
              flight_id: fid,
              airline: airline || 'Unknown',
              type: 'arrival',
              terminal: terminal || 'T2',
              gate: null,
              check_in: null,
              timings,
              status: status || 'unknown',
              category: 'commercial',
              source_url: 'https://csmia-mumbai.adaniairports.com/en/flight-status',
            };
          }

          timings.boarding = '';
          return {
            flight_id: fid,
            airline: airline || 'Unknown',
            type: 'departure',
            terminal: terminal || 'T2',
            gate: extraCol || null,
            check_in: null,
            timings,
            status: status || 'unknown',
            category: 'commercial',
            source_url: 'https://csmia-mumbai.adaniairports.com/en/flight-status',
          };
        })
        .filter(Boolean);
    },
    { sel: tableBodySelector, leg: legType },
  );
}

async function dismissCookieBanner(page) {
  const accept = page.locator('#cookieConsentBanner #primaryButton');
  try {
    await accept.waitFor({ state: 'visible', timeout: 8000 });
    await accept.click();
    await page.waitForTimeout(400);
  } catch {
    /* already dismissed or not shown */
  }
}

async function dismissPromoBannerModal(page) {
  const modal = page.locator('#bannerModal.show');
  if (!(await modal.isVisible().catch(() => false))) return;
  const close = modal.locator('.closeBannerModal, [data-bs-dismiss="modal"]').first();
  await close.click({ timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(300);
}

async function loadAllRows(page, tableBodySelector, legType) {
  for (let i = 0; i < 8; i++) {
    const more = page.locator('.floadMore').first();
    if (!(await more.isVisible().catch(() => false))) break;
    const countBefore = await page.$$eval(`${tableBodySelector} .flightListRow`, (rows) => rows.length);
    await more.click().catch(() => {});
    await page.waitForTimeout(1500);
    const countAfter = await page.$$eval(`${tableBodySelector} .flightListRow`, (rows) => rows.length);
    if (countAfter <= countBefore) break;
  }
  return collectFromDom(page, tableBodySelector, legType);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(SOURCE_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await dismissCookieBanner(page);
  await dismissPromoBannerModal(page);
  await page.waitForSelector('#arrivalFlightsTableBody .flightListRow', { timeout: 30000 });

  const arrivals = await loadAllRows(page, '#arrivalFlightsTableBody', 'arrival');

  await dismissPromoBannerModal(page);
  await page.locator('a#departure.flight-nav-link').first().click();
  await page.waitForTimeout(800);
  await page.waitForSelector('#departureFlightsTableBody', { timeout: 15000 });

  const noResult = page.locator('#departureFlightsTableBody #no-result');
  let departures = [];
  if (await noResult.isVisible().catch(() => false)) {
    departures = [];
  } else {
    await page
      .waitForSelector('#departureFlightsTableBody .flightListRow', { timeout: 20000 })
      .catch(() => {});
    departures = await loadAllRows(page, '#departureFlightsTableBody', 'departure');
  }

  await browser.close();

  const now = new Date().toISOString();
  const flights = [...arrivals, ...departures].map((f) => ({
    ...f,
    last_verified_at: now,
  }));

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(flights, null, 2), 'utf8');
  console.log(`Wrote ${flights.length} flights to ${OUT}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
