import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { lotusEase } from '../utils/lotusMotion';

/**
 * Slide-over chat — does NOT steal layout width from main content.
 */
export default function ChatDrawer({ open, onClose, children }) {
  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.button
            type="button"
            className="chat-drawer-scrim"
            aria-label="Close assistant"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />
          <motion.aside
            className="chat-drawer"
            role="dialog"
            aria-label="AirHelp assistant"
            aria-modal="true"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.32, ease: lotusEase }}
          >
            {children}
          </motion.aside>
        </>
      ) : null}
    </AnimatePresence>
  );
}
