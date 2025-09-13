import axios from 'axios'

export type SuggestionAction =
  | { type: 'addNode'; node: Record<string, unknown> }
  | { type: 'updateParameter'; node: string; parameter: string; value: unknown }

export async function requestSuggestions(prompt: string): Promise<SuggestionAction[]> {
  const url = process.env.LLM_API_URL
  if (!url) throw new Error('LLM_API_URL missing')
  const headers: Record<string, string> = {}
  if (process.env.LLM_API_KEY) headers.Authorization = `Bearer ${process.env.LLM_API_KEY}`
  const { data } = await axios.post(url, { prompt }, { headers })
  return Array.isArray(data.actions) ? data.actions : []
}
