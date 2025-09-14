import { setModelProvider, getModelProvider } from '../src/model-provider';

describe('model provider', () => {
        it('stores provider config', () => {
                setModelProvider({ provider: 'openai-o4-mini', apiKey: 'key' });
                expect(getModelProvider()).toEqual({ provider: 'openai-o4-mini', apiKey: 'key' });
        });
});
