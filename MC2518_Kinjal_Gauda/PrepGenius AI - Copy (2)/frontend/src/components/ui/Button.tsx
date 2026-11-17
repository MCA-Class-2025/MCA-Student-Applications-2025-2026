import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'glow';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  icon,
  className = '',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed';

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
  };

  const variantStyles = {
    primary: 'bg-gradient-to-r from-brand-indigo to-brand-violet text-white hover:opacity-95 shadow-lg shadow-brand-indigo/25 border border-brand-indigo/30',
    secondary: 'bg-dark-surface text-dark-text hover:bg-dark-hover border border-dark-border',
    outline: 'bg-transparent text-dark-text border border-dark-border hover:bg-dark-surface/50 hover:border-brand-indigo/40',
    ghost: 'bg-transparent text-dark-muted hover:text-dark-text hover:bg-dark-surface/50',
    glow: 'bg-gradient-to-r from-brand-indigo via-brand-violet to-brand-cyan text-white shadow-lg shadow-brand-violet/30 border border-white/20 animate-pulse-slow',
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </motion.button>
  );
};
