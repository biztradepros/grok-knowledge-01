import { createRefinerySite, prepareRefineryAdvance } from './refinery-07.fixture.js';
import { createSkillAiSite, prepareSkillAiAdvance } from './skill-ai-09.fixture.js';
import { createSocialCardSite, prepareSocialCardAdvance } from './social-card-04.fixture.js';

// Order follows the portability plan: 9 (non-deterministic) -> 7 (gates/HOLD) -> 4 (human gate).
export const SITE_FIXTURES = [
  { key: 'F09', makeSite: createSkillAiSite, prepareAdvance: prepareSkillAiAdvance },
  { key: 'F07', makeSite: createRefinerySite, prepareAdvance: prepareRefineryAdvance },
  { key: 'F04', makeSite: createSocialCardSite, prepareAdvance: prepareSocialCardAdvance },
];
