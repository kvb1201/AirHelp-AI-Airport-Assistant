import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { lotusEase } from '../../utils/lotusMotion';

export default function Reveal({
  children,
  className = '',
  delay = 0,
  y = 28,
  as: Tag = 'div',
}) {
  const reduce = useReducedMotion();
  const MotionTag = typeof Tag === 'string' ? motion[Tag] || motion.div : motion.div;

  if (reduce) {
    const Static = Tag;
    return <Static className={className}>{children}</Static>;
  }

  return (
    <MotionTag
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-8% 0px' }}
      transition={{ duration: 0.55, delay, ease: lotusEase }}
    >
      {children}
    </MotionTag>
  );
}
