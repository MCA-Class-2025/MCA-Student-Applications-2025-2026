import React from 'react';
import { motion } from 'framer-motion';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  glowColor?: 'indigo' | 'violet' | 'emerald' | 'cyan';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverEffect = true,
  glowColor = 'indigo',
}) => {
  const glowBorderMap = {
    indigo: 'hover:border-brand-indigo/40 hover:shadow-brand-indigo/10',
    violet: 'hover:border-brand-violet/40 hover:shadow-brand-violet/10',
    emerald: 'hover:border-brand-emerald/40 hover:shadow-brand-emerald/10',
    cyan: 'hover:border-brand-cyan/40 hover:shadow-brand-cyan/10',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`glass-card rounded-2xl p-6 transition-all duration-300 ${
        hoverEffect ? `glass-card-hover ${glowBorderMap[glowColor]}` : ''
      } ${className}`}
    >
      {children}
    </motion.div>
  );
};
