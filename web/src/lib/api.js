const API_BASE = (import.meta.env.VITE_API_BASE ?? '').trim();

async function fetchApi(path, options = {}) {
  if (!API_BASE) {
    throw new Error('API not configured. Set VITE_API_BASE in .env (e.g. http://localhost:8000).');
  }
  const { method = 'GET', body, timeout = 15000 } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `API error: ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    if (e.name === 'AbortError') {
      throw new Error('Request timed out. The API may be slow or unreachable.');
    }
    if (e.message === 'Failed to fetch' || (e instanceof TypeError && e.message?.includes('fetch'))) {
      throw new Error(
        `Cannot reach the API at ${API_BASE}. Make sure the backend is running (e.g. run "uvicorn app.main:app --reload --port 8000" in the api folder).`
      );
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

// Career Pathfinder
export const getRoles = () => fetchApi('/api/v1/career/roles');
export const getCertifications = () => fetchApi('/api/v1/career/certifications');
export const getTargets = () => fetchApi('/api/v1/career/targets');
export const generateRoadmap = (inputs) =>
  fetchApi('/api/v1/roadmap/generate', { method: 'POST', body: inputs, timeout: 30000 });

// SkillBridge
export const getPrograms = (params = {}) =>
  fetchApi(`/api/v1/programs?${new URLSearchParams(params)}`);
export const getProgram = (id) => fetchApi(`/api/v1/programs/${id}`);
export const getProgramsMap = (params = {}) =>
  fetchApi(`/api/v1/programs/map?${new URLSearchParams(params)}`);
export const getProgramStats = () => fetchApi('/api/v1/programs/stats');

// Scrubbed ERG fallback when API/DB unavailable (matches FOB Legacy ergsApi.js)
const ERG_FALLBACK = {
  total: 5,
  page: 1,
  per_page: 20,
  ergs: [
    { id: '1', company_name: 'Microsoft', erg_name: 'Military at Microsoft', industry: 'Technology', has_skillbridge: true, military_friendly_rating: 'top_employer', description: 'Microsoft Military Affairs helps veterans transition into the tech industry with specialized training and a robust internal community.', offerings: ['skillbridge_partner', 'mentorship', 'networking'], company_website: 'https://microsoft.com', careers_url: 'https://careers.microsoft.com/military' },
    { id: '2', company_name: 'Lockheed Martin', erg_name: 'Military Veterans Network', industry: 'Defense Contracting', has_skillbridge: true, military_friendly_rating: 'gold', description: 'The Military Veterans Network connects former service members across Lockheed Martin, providing career development and camaraderie.', offerings: ['networking', 'career_development', 'community_service'], company_website: 'https://lockheedmartin.com' },
    { id: '3', company_name: 'Booz Allen Hamilton', erg_name: 'Armed Services Network', industry: 'Consulting', has_skillbridge: true, military_friendly_rating: 'top_employer', description: "Booz Allen's Armed Services Network supports veterans and military spouses with mentorship, networking, and transition support.", offerings: ['mentorship', 'spouse_support', 'transition_support'], company_website: 'https://boozallen.com' },
    { id: '4', company_name: 'Amazon', erg_name: 'Warriors@Amazon', industry: 'Technology', has_skillbridge: true, military_friendly_rating: 'gold', description: 'Warriors@Amazon offers a massive internal network for veterans, complete with customized training and a dedicated SkillBridge pipeline.', offerings: ['skillbridge_partner', 'training_program', 'networking'], company_website: 'https://amazon.com' },
    { id: '5', company_name: 'JPMorgan Chase', erg_name: 'Veterans Resource Group', industry: 'Finance', has_skillbridge: true, military_friendly_rating: 'silver', description: 'JPMC provides a welcoming environment for veterans with a dedicated focus on networking, professional growth, and military spouse support.', offerings: ['career_development', 'spouse_support', 'networking'], company_website: 'https://jpmorganchase.com' },
  ],
};

// Communities, ERGs, News, Networking
export const getCommunities = (params = {}) =>
  fetchApi(`/api/v1/communities?${new URLSearchParams(params)}`);
export async function getERGs(params = {}) {
  try {
    return await fetchApi(`/api/v1/ergs?${new URLSearchParams(params)}`);
  } catch {
    return ERG_FALLBACK;
  }
}
export const getNews = (params = {}) =>
  fetchApi(`/api/v1/news?${new URLSearchParams(params)}`);
export const analyzeNetwork = (data) =>
  fetchApi('/api/v1/networking/analyze', { method: 'POST', body: data, timeout: 30000 });
export const generateNetworkingRoadmap = (data) =>
  fetchApi('/api/v1/networking/roadmap', { method: 'POST', body: data, timeout: 30000 });
