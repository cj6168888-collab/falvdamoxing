import { describe, expect, it } from 'vitest';
import { audienceFromSlug, audiencePublicCopy, audienceSlugs } from './public-site-copy';

describe('public-site-copy', () => {
  it('maps public slugs to tenant types', () => {
    expect(audienceFromSlug('law-firm')).toBe('law_firm');
    expect(audienceFromSlug('enterprise')).toBe('enterprise');
    expect(audienceFromSlug('personal')).toBe('personal');
    expect(audienceFromSlug('unknown')).toBeUndefined();
  });

  it('keeps the core positioning for enterprise and personal users', () => {
    expect(audiencePublicCopy.enterprise.headline).toBe('让任何企业拥有靠谱的法律顾问');
    expect(audiencePublicCopy.personal.headline).toBe('做你的法律后盾，先帮你稳住局面');
    expect(audiencePublicCopy.personal.subhead).not.toContain('律师推荐');
  });

  it('keeps register route slugs stable', () => {
    expect(audienceSlugs.law_firm).toBe('law-firm');
    expect(audienceSlugs.enterprise).toBe('enterprise');
    expect(audienceSlugs.personal).toBe('personal');
  });
});
