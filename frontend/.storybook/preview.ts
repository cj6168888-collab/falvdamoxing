import type { Preview } from '@storybook/react-vite'
import '../src/styles/globals.css'

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
       color: /(background|color)$/i,
       date: /Date$/i,
      },
    },

    a11y: {
      test: 'todo'
    },

    darkMode: {
      classTarget: 'html',
      stylePreview: true,
      dark: { class: 'dark' },
      light: { class: 'light' },
    },
  },

  decorators: [
    (Story) => (
      <div className="p-4">
        <Story />
      </div>
    ),
  ],
};

export default preview;