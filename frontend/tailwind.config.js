/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        mtn: {
          yellow: '#FFCC00',
          'yellow-soft': '#FFE680',
          'yellow-deep': '#F5A800',
          blue: '#003087',
          'blue-light': '#1E4DB7',
          'blue-deep': '#001A4D',
          dark: '#0F172A',
          light: '#F8FAFC',
          ink: '#1E293B',
        },
        surface: {
          0: '#FFFFFF',
          50: '#FAFAFB',
          100: '#F4F4F7',
          200: '#E5E7EB',
        },
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
      },
      fontSize: {
        'a11y-sm': '0.9rem',
        'a11y-base': '1.1rem',
        'a11y-lg': '1.3rem',
        'a11y-xl': '1.6rem',
      },
      borderRadius: {
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      boxShadow: {
        'soft': '0 2px 12px -2px rgba(15, 23, 42, 0.06), 0 1px 3px -1px rgba(15, 23, 42, 0.04)',
        'lift': '0 10px 30px -10px rgba(15, 23, 42, 0.15), 0 4px 12px -6px rgba(15, 23, 42, 0.08)',
        'glow-yellow': '0 8px 28px -8px rgba(255, 204, 0, 0.55)',
        'glow-blue': '0 8px 28px -8px rgba(0, 48, 135, 0.45)',
      },
      backgroundImage: {
        'mesh-1': 'radial-gradient(at 20% 20%, rgba(255, 204, 0, 0.18) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(0, 48, 135, 0.15) 0px, transparent 50%), radial-gradient(at 0% 80%, rgba(255, 230, 128, 0.18) 0px, transparent 50%)',
        'mesh-2': 'radial-gradient(at 80% 20%, rgba(0, 48, 135, 0.18) 0px, transparent 50%), radial-gradient(at 0% 100%, rgba(255, 204, 0, 0.20) 0px, transparent 50%)',
        'gold-sheen': 'linear-gradient(135deg, #FFCC00 0%, #FFD84D 50%, #F5A800 100%)',
        'night-sheen': 'linear-gradient(135deg, #003087 0%, #1E4DB7 60%, #001A4D 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.35s ease-out',
        'slide-up': 'slideUp 0.4s cubic-bezier(0.22, 1, 0.36, 1)',
        'pulse-soft': 'pulseSoft 2.4s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s linear infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: 0, transform: 'translateY(6px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
        slideUp: {
          from: { opacity: 0, transform: 'translateY(14px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(255, 204, 0, 0.45)' },
          '50%': { boxShadow: '0 0 0 10px rgba(255, 204, 0, 0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}