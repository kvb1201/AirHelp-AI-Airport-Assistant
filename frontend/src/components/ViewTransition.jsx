import React, { useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { lotusEase, viewDirection } from '../utils/lotusMotion';

export default function ViewTransition({ viewKey, children, className = '', enabled = true }) {
  const prevKey = useRef(viewKey);
  const direction = viewDirection(prevKey.current, viewKey);
  prevKey.current = viewKey;

  if (!enabled) {
    return <div className={`view-stage ${className}`.trim()}>{children}</div>;
  }

  const reduced =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const variants = reduced
    ? {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
      }
    : {
        initial: (d) => ({ opacity: 0, x: d * 16 }),
        animate: { opacity: 1, x: 0 },
        exit: (d) => ({ opacity: 0, x: d * -12 }),
      };

  return (
    <motion.div className={`view-stage ${className}`.trim()} initial={false}>
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={viewKey}
          className="view-stage-inner"
          custom={direction}
          variants={variants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{ duration: reduced ? 0.12 : 0.28, ease: lotusEase }}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}
