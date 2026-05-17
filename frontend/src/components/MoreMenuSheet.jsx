import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { lotusSpring } from '../utils/lotusMotion';

const ITEMS = [
  { id: 'facilities', label: 'Facilities', sub: 'Food, shops, lounges', icon: 'apartment' },
  { id: 'lostfound', label: 'Lost & Found', sub: 'Report or claim items', icon: 'luggage' },
  { id: 'profile', label: 'Profile', sub: 'Preferences & account', icon: 'account_circle' },
  { id: 'operator', label: 'Operator', sub: 'Staff console', icon: 'admin_panel_settings' },
];

export default function MoreMenuSheet({ open, onClose, onSelect }) {
  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.button
            type="button"
            className="more-menu-scrim"
            aria-label="Close menu"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />
          <motion.div
            className="more-menu-sheet lotus-glass-dock"
            role="menu"
            aria-label="More options"
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            transition={lotusSpring}
          >
            {ITEMS.map((item) => (
              <button
                key={item.id}
                type="button"
                className="more-menu-item"
                role="menuitem"
                onClick={() => {
                  onSelect(item.id);
                  onClose();
                }}
              >
                <span className="ms" aria-hidden="true">{item.icon}</span>
                <div>
                  <motion.div className="more-menu-item-title">{item.label}</motion.div>
                  <motion.div className="more-menu-item-sub">{item.sub}</motion.div>
                </div>
              </button>
            ))}
          </motion.div>
        </>
      ) : null}
    </AnimatePresence>
  );
}
