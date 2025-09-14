import { o4mini, gpt41mini, gpt41, anthropicClaudeSonnet4, LLMProviderConfig } from './llm-config';

export type ModelProvider = 'openai-o4-mini' | 'openai-gpt-4.1-mini' | 'openai-gpt-4.1' | 'anthropic-claude-sonnet-4';

interface ProviderConfig extends LLMProviderConfig {
        provider: ModelProvider;
}

let currentConfig: ProviderConfig | null = null;

export const setModelProvider = (config: ProviderConfig) => {
        currentConfig = config;
};

export const getModelProvider = () => currentConfig;

export const createModel = async () => {
        if (!currentConfig) throw new Error('Model provider is not configured');
        const { provider, ...rest } = currentConfig;
        switch (provider) {
                case 'openai-o4-mini':
                        return o4mini(rest);
                case 'openai-gpt-4.1-mini':
                        return gpt41mini(rest);
                case 'openai-gpt-4.1':
                        return gpt41(rest);
                case 'anthropic-claude-sonnet-4':
                        return anthropicClaudeSonnet4(rest);
        }
};

const envProvider = process.env.N8N_AI_PROVIDER as ModelProvider | undefined;
const envKey = process.env.N8N_AI_API_KEY;
if (envProvider && envKey) {
        setModelProvider({ provider: envProvider, apiKey: envKey, baseUrl: process.env.N8N_AI_BASE_URL });
}
