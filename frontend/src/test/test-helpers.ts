import userEvent from '@testing-library/user-event';

export function createUser(): ReturnType<typeof userEvent.setup> {
  return userEvent.setup();
}

export async function fillForm(
  user: ReturnType<typeof userEvent.setup>,
  fields: Record<string, string>
): Promise<void> {
  for (const [label, value] of Object.entries(fields)) {
    const input = document.querySelector(`[aria-label="${label}"], label:has-text("${label}") input, input[name="${label}"]`);
    if (input) {
      await user.clear(input as HTMLElement);
      await user.type(input as HTMLElement, value);
    }
  }
}

export async function selectOption(
  user: ReturnType<typeof userEvent.setup>,
  label: string,
  option: string
): Promise<void> {
  const select = document.querySelector(`[aria-label="${label}"], select[name="${label}"]`);
  if (select) {
    await user.selectOptions(select as HTMLSelectElement, option);
  }
}

export async function clickButton(
  user: ReturnType<typeof userEvent.setup>,
  text: string
): Promise<void> {
  const button = document.querySelector(`button:has-text("${text}")`);
  if (button) {
    await user.click(button as HTMLElement);
  }
}

export function getTestId(id: string): HTMLElement {
  const element = document.querySelector(`[data-testid="${id}"]`);
  if (!element) throw new Error(`Element with testid "${id}" not found`);
  return element as HTMLElement;
}

export function queryTestId(id: string): HTMLElement | null {
  return document.querySelector(`[data-testid="${id}"]`) as HTMLElement | null;
}

export async function waitForElement(
  callback: () => HTMLElement | null,
  timeout = 5000
): Promise<HTMLElement> {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const element = callback();
    if (element) return element;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw new Error('Element not found within timeout');
}
