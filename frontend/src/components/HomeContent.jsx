import React, { useState, useRef, useEffect, useLayoutEffect } from 'react';
import BoardingPassUpload from './BoardingPassUpload';
import MarqueeBand from './home/MarqueeBand';
import HeroAnimated from './home/HeroAnimated';
import PromoStrip from './home/PromoStrip';
import ScrollHeadline from './home/ScrollHeadline';
import StoryAnimated from './home/StoryAnimated';
import HomeSection from './home/HomeSection';
import PillarShowcase from './home/PillarShowcase';
import StatsBand from './home/StatsBand';
import ReviewsCarousel from './home/ReviewsCarousel';
import FinaleStrip from './home/FinaleStrip';
import GsapReveal from './home/GsapReveal';
import GsapStagger from './home/GsapStagger';
import { ScrollTrigger, refreshHomeScroll } from '../lib/gsapSetup';

const PRIMARY_ACTIONS = [
  { id: 'ask', label: 'Ask AirHelp', desc: 'Flights, gates, lounges', icon: 'forum', primary: true, action: 'ask' },
  { id: 'nav', label: 'Get directions', desc: 'Walking routes in T2', icon: 'directions_walk', action: 'navigation' },
  { id: 'map', label: 'Terminal map', desc: 'See where you are', icon: 'map', action: 'floor_map' },
  { id: 'flight', label: 'My flight', desc: 'Scan boarding pass', icon: 'qr_code_scanner', action: 'flight_queries' },
];

const PILLARS = [
  { title: 'Live intelligence', body: 'Real-time flight status, gate changes, and boarding cues — not static boards you chase down.', icon: 'flight_takeoff' },
  { title: 'Indoor navigation', body: 'Step-by-step walking routes across Terminal 2, tuned to where you actually are.', icon: 'route' },
  { title: 'Natural conversation', body: 'Ask in plain language — “take me to BIBA”, “nearest lounge”, “my gate”. Voice or text.', icon: 'forum' },
  { title: 'Boarding pass scan', body: 'Upload once — we read flight, gate, and seat, then guide you from there.', icon: 'qr_code_scanner' },
  { title: 'Facilities discovery', body: 'Food, shops, lounges, and services — filtered by what matters to you right now.', icon: 'storefront' },
  { title: 'Issue reporting', body: 'Report problems with a ticket reference — airport staff can follow up.', icon: 'support_agent' },
];

const PROMPTS = [
  { label: 'Flight status', icon: 'flight_takeoff', message: 'What is the status of my flight?' },
  { label: 'Nearest lounge', icon: 'weekend', message: 'Where is the nearest lounge?' },
  { label: 'Gate directions', icon: 'signpost', message: 'How do I get to my gate?' },
  { label: 'Report issue', icon: 'report_problem', action: 'report_issue' },
];

const DEPARTURES = [
  { flight: 'AI-202', dest: 'Delhi', gate: 'B14', time: '16:45', status: 'ON TIME' },
  { flight: '6E-851', dest: 'Bangalore', gate: 'C7', time: '17:10', status: 'BOARDING' },
  { flight: 'UK-972', dest: 'London', gate: 'D3', time: '17:30', status: 'ON TIME' },
  { flight: 'EK-503', dest: 'Dubai', gate: 'E11', time: '18:00', status: 'DELAYED' },
  { flight: 'SG-181', dest: 'Hyderabad', gate: 'B9', time: '18:20', status: 'ON TIME' },
];

const REVIEWS = [
  { quote: 'Found my gate in under a minute — no more squinting at departure screens from across the hall.', author: 'Priya M.', context: 'Domestic departure' },
  { quote: 'Asked for the nearest lounge and got walking directions that actually matched the terminal layout.', author: 'Rahul K.', context: 'International transit' },
  { quote: 'Uploaded my boarding pass and AirHelp had my gate ready before I reached security.', author: 'Ananya S.', context: 'Evening departure' },
];

const TIPS = [
  { icon: 'schedule', title: 'Arrive early', body: 'Allow 2–3 hours for international departures at peak times.' },
  { icon: 'luggage', title: 'Baggage', body: 'Liquids in carry-on must be under 100ml in a clear bag.' },
  { icon: 'wifi', title: 'Free Wi-Fi', body: 'Connect to CSMIA_Free_WiFi — verify with your mobile number.' },
];

function statusClass(status) {
  if (status === 'BOARDING') return 'fids-board__status--boarding';
  if (status === 'DELAYED') return 'fids-board__status--delay';
  return 'fids-board__status--ok';
}

export default function HomeContent({
  locationLabel = 'Near Entrance',
  onSend,
  onOpenNavigation,
  onOpenFloorMap,
  onOpenReportIssue,
  onOpenFlightQueries,
  onOpenChat,
}) {
  const askRef = useRef(null);
  const [askValue, setAskValue] = useState('');

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  useLayoutEffect(() => {
    refreshHomeScroll();
    return () => {
      ScrollTrigger.defaults({ scroller: window });
      ScrollTrigger.refresh();
    };
  }, []);

  useEffect(() => {
    const scroller =
      document.querySelector('.view-stage-inner') ||
      document.querySelector('.main-content--home') ||
      document.querySelector('.main-content');

    const refresh = () => refreshHomeScroll();
    const t1 = setTimeout(refresh, 300);
    const t2 = setTimeout(refresh, 1200);
    const t3 = setTimeout(refresh, 2500);
    window.addEventListener('load', refresh);
    window.addEventListener('resize', refresh);
    scroller?.addEventListener('scroll', refresh, { passive: true });

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      window.removeEventListener('load', refresh);
      window.removeEventListener('resize', refresh);
      scroller?.removeEventListener('scroll', refresh);
    };
  }, []);

  const submitAsk = (text) => {
    const t = (text || askValue).trim();
    if (!t || !onSend) return;
    onSend(t, null);
    setAskValue('');
  };

  const handlePrimary = (item) => {
    if (item.action === 'ask') {
      if (onOpenChat) onOpenChat();
      else askRef.current?.focus();
      return;
    }
    if (item.action === 'navigation' && onOpenNavigation) {
      onOpenNavigation();
      return;
    }
    if (item.action === 'floor_map' && onOpenFloorMap) {
      onOpenFloorMap(null);
      return;
    }
    if (item.action === 'flight_queries' && onOpenFlightQueries) {
      onOpenFlightQueries();
    }
  };

  const handlePrompt = (p) => {
    if (p.action === 'report_issue') {
      if (onOpenReportIssue) onOpenReportIssue();
      else if (onSend) onSend('I need to report an issue.', null);
      return;
    }
    if (onSend) onSend(p.message, null);
  };

  return (
    <div className="home-experience">
      <HeroAnimated
        greeting={greeting}
        locationLabel={locationLabel}
        askValue={askValue}
        onAskChange={setAskValue}
        onAskSubmit={() => submitAsk()}
        askRef={askRef}
        prompts={PROMPTS}
        onPrompt={handlePrompt}
      />

      <PromoStrip />
      <ScrollHeadline />

      <div className="hx-zone hx-zone--body">
        <MarqueeBand items={['ASK', 'NAVIGATE', 'FLY', 'RELAX', 'DISCOVER']} />

        <StoryAnimated onOpenChat={onOpenChat} />

        <HomeSection
          id="capabilities-title"
          tag="Capabilities"
          title="Everything you need in one place"
          lead="Tap a capability — same assistant behind each path."
          className="hx-block--pillars"
        >
          <PillarShowcase pillars={PILLARS} hideHeader />
        </HomeSection>

        <StatsBand />

        <HomeSection
          id="actions-title"
          tag="01"
          title="What do you need right now?"
          lead="Four quick paths into the same assistant."
          className="hx-section--actions"
        >
          <GsapStagger selector=".hx-action-card" className="hx-action-grid">
            {PRIMARY_ACTIONS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`hx-action-card gsap-stagger-item${item.primary ? ' hx-action-card--primary' : ''}`}
                onClick={() => handlePrimary(item)}
              >
                <span className="hx-action-icon" aria-hidden="true">
                  <span className="ms">{item.icon}</span>
                </span>
                <span className="hx-action-label">{item.label}</span>
                <span className="hx-action-desc">{item.desc}</span>
              </button>
            ))}
          </GsapStagger>
        </HomeSection>

        <HomeSection
          id="departures-title"
          tag="02"
          title="Live departures"
          lead="Terminal 2 board — ask AirHelp for your specific flight."
          className="hx-section--fids"
        >
          <GsapReveal delay={0.05}>
            <div className="hx-fids-tabs" role="tablist" aria-label="Departure categories">
              <span className="hx-fids-tab hx-fids-tab--active" role="tab" aria-selected="true">All flights</span>
              <span className="hx-fids-tab" role="tab">Domestic</span>
              <span className="hx-fids-tab" role="tab">International</span>
            </div>
          </GsapReveal>
          <GsapStagger selector=".fids-board__row" stagger={0.05} y={16}>
            <div className="hx-fids fids-board hx-surface">
                <div className="fids-board__header">
                  <span>Flight</span>
                  <span>Destination</span>
                  <span>Gate</span>
                  <span>Time</span>
                  <span>Status</span>
                </div>
                {DEPARTURES.map((d) => (
                  <div key={d.flight} className="fids-board__row gsap-stagger-item">
                    <span className="fids-board__flight">{d.flight}</span>
                    <span className="fids-board__dest">{d.dest}</span>
                    <span className="fids-board__gate">{d.gate}</span>
                    <span className="fids-board__time">{d.time}</span>
                    <span className={`fids-board__status ${statusClass(d.status)}`}>{d.status}</span>
                  </div>
                ))}
            </div>
          </GsapStagger>
        </HomeSection>

        <HomeSection
          id="boarding-title"
          tag="03"
          title="Scan your boarding pass"
          lead="We read flight, gate, and seat — then guide you from where you are."
          className="hx-section--boarding"
        >
          <GsapReveal variant="scaleIn">
            <div className="hx-boarding-block hx-surface">
              <BoardingPassUpload
                onBoardingPassProcessed={(data) => {
                  if (onSend) {
                    onSend(
                      `I've uploaded my boarding pass. Flight: ${data.flight_number}, Gate: ${data.gate}, Seat: ${data.seat}. Can you help me navigate?`,
                      null,
                    );
                  }
                }}
              />
            </div>
          </GsapReveal>
        </HomeSection>

        <ReviewsCarousel reviews={REVIEWS} />

        <HomeSection id="tips-title" tag="04" title="Before you go" className="hx-section--tips">
          <GsapStagger selector=".hx-tip-card" className="hx-tips-scroll">
            {TIPS.map((tip) => (
              <article key={tip.title} className="hx-tip-card hx-surface gsap-stagger-item">
                <span className="ms">{tip.icon}</span>
                <h3 className="hx-tip-title">{tip.title}</h3>
                <p className="hx-tip-body">{tip.body}</p>
              </article>
            ))}
          </GsapStagger>
        </HomeSection>
      </div>

      <FinaleStrip onOpenChat={onOpenChat} />
    </div>
  );
}
