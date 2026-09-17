/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./hpp/templates/**/*.html",
    "./templates/**/*.html",
    "./hpp/**/*.py",
    "./config/**/*.py",
  ],
  safelist: [
    {
      pattern: /(bg|text|border)-(slate|purple|blue|indigo|amber|teal|rose|cyan|emerald|violet|pink)-(50|100|200|300|400|500|600|700|800|900)/,
    },
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
