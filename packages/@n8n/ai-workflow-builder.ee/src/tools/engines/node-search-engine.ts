import type { INodeTypeDescription, NodeConnectionType } from 'n8n-workflow';
import { NodeConnectionTypes } from 'n8n-workflow';

import type { NodeSearchResult } from '../../types/nodes';

export const SCORE_WEIGHTS = {
        NAME_CONTAINS: 10,
        DISPLAY_NAME_CONTAINS: 8,
        DESCRIPTION_CONTAINS: 5,
        ALIAS_CONTAINS: 8,
        NAME_EXACT: 20,
        DISPLAY_NAME_EXACT: 15,
        CONNECTION_EXACT: 100,
        CONNECTION_IN_EXPRESSION: 50,
} as const;

type ProcessedNode = {
        node: INodeTypeDescription;
        normalizedName: string;
        normalizedDisplayName: string;
        normalizedDescription: string;
        normalizedAlias: string[];
};

export class NodeSearchEngine {
        private processed: ProcessedNode[];
        private nameSearchCache = new Map<string, NodeSearchResult[]>();
        private connectionSearchCache = new Map<string, NodeSearchResult[]>();

        constructor(nodeTypes: INodeTypeDescription[]) {
                this.processed = nodeTypes.map((nt) => ({
                        node: nt,
                        normalizedName: NodeSearchEngine.normalize(nt.name),
                        normalizedDisplayName: NodeSearchEngine.normalize(nt.displayName),
                        normalizedDescription: nt.description
                                ? NodeSearchEngine.normalize(nt.description)
                                : '',
                        normalizedAlias:
                                nt.codex?.alias?.map((a) => NodeSearchEngine.normalize(a)) ?? [],
                }));
        }

        private static normalize(text: string): string {
                return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        }

        /**
         * Search nodes by name, display name, or description
         * @param query - The search query string
         * @param limit - Maximum number of results to return
         * @returns Array of matching nodes sorted by relevance
         */
        searchByName(query: string, limit: number = 20): NodeSearchResult[] {
                const normalizedQuery = NodeSearchEngine.normalize(query);
                const key = `${normalizedQuery}|${limit}`;
                const cached = this.nameSearchCache.get(key);
                if (cached) return cached;
                const results: NodeSearchResult[] = [];
                for (const p of this.processed) {
                        try {
                                const score = this.calculateNameScore(p, normalizedQuery);
                                if (score > 0) results.push(this.createSearchResult(p.node, score));
                        } catch (error) {}
                }
                const sorted = this.sortAndLimit(results, limit);
                this.nameSearchCache.set(key, sorted);
                return sorted;
        }

        /**
         * Search for sub-nodes that output a specific connection type
         * @param connectionType - The connection type to search for
         * @param limit - Maximum number of results
         * @param nameFilter - Optional name filter
         * @returns Array of matching sub-nodes
         */
        searchByConnectionType(
                connectionType: NodeConnectionType,
                limit: number = 20,
                nameFilter?: string,
        ): NodeSearchResult[] {
                const normalizedFilter = nameFilter ? NodeSearchEngine.normalize(nameFilter) : undefined;
                const key = `${connectionType}|${normalizedFilter ?? ''}|${limit}`;
                const cached = this.connectionSearchCache.get(key);
                if (cached) return cached;
                const results: NodeSearchResult[] = [];
                for (const p of this.processed) {
                        try {
                                const connectionScore = this.getConnectionScore(p.node, connectionType);
                                if (connectionScore > 0) {
                                        const nameScore = normalizedFilter ? this.calculateNameScore(p, normalizedFilter) : 0;
                                        if (!normalizedFilter || nameScore > 0) {
                                                const totalScore = connectionScore + nameScore;
                                                results.push(this.createSearchResult(p.node, totalScore));
                                        }
                                }
                        } catch (error) {}
                }
                const sorted = this.sortAndLimit(results, limit);
                this.connectionSearchCache.set(key, sorted);
                return sorted;
        }

	/**
	 * Format search results for tool output
	 * @param result - Single search result
	 * @returns XML-formatted string
	 */
	formatResult(result: NodeSearchResult): string {
		return `
		<node>
			<node_name>${result.name}</node_name>
			<node_description>${result.description}</node_description>
			<node_inputs>${typeof result.inputs === 'object' ? JSON.stringify(result.inputs) : result.inputs}</node_inputs>
			<node_outputs>${typeof result.outputs === 'object' ? JSON.stringify(result.outputs) : result.outputs}</node_outputs>
		</node>`;
	}

        private calculateNameScore(node: ProcessedNode, normalizedQuery: string): number {
                let score = 0;
                if (node.normalizedName.includes(normalizedQuery)) score += SCORE_WEIGHTS.NAME_CONTAINS;
                if (node.normalizedDisplayName.includes(normalizedQuery)) score += SCORE_WEIGHTS.DISPLAY_NAME_CONTAINS;
                if (node.normalizedDescription.includes(normalizedQuery)) score += SCORE_WEIGHTS.DESCRIPTION_CONTAINS;
                if (node.normalizedAlias.some((alias) => alias.includes(normalizedQuery))) score += SCORE_WEIGHTS.ALIAS_CONTAINS;
                if (node.normalizedName === normalizedQuery) score += SCORE_WEIGHTS.NAME_EXACT;
                if (node.normalizedDisplayName === normalizedQuery) score += SCORE_WEIGHTS.DISPLAY_NAME_EXACT;
                return score;
        }

	/**
	 * Check if a node has a specific connection type in outputs
	 * @param nodeType - Node type to check
	 * @param connectionType - Connection type to look for
	 * @returns Score indicating match quality
	 */
	private getConnectionScore(
		nodeType: INodeTypeDescription,
		connectionType: NodeConnectionType,
	): number {
		const outputs = nodeType.outputs;

		if (Array.isArray(outputs)) {
			// Direct array match
			if (outputs.includes(connectionType)) {
				return SCORE_WEIGHTS.CONNECTION_EXACT;
			}
		} else if (typeof outputs === 'string') {
			// Expression string - check if it contains the connection type
			if (outputs.includes(connectionType)) {
				return SCORE_WEIGHTS.CONNECTION_IN_EXPRESSION;
			}
		}

		return 0;
	}

	/**
	 * Create a search result object
	 * @param nodeType - Node type description
	 * @param score - Calculated score
	 * @returns Search result object
	 */
	private createSearchResult(nodeType: INodeTypeDescription, score: number): NodeSearchResult {
		return {
			name: nodeType.name,
			displayName: nodeType.displayName,
			description: nodeType.description ?? 'No description available',
			inputs: nodeType.inputs,
			outputs: nodeType.outputs,
			score,
		};
	}

	/**
	 * Sort and limit search results
	 * @param results - Array of results
	 * @param limit - Maximum number to return
	 * @returns Sorted and limited results
	 */
	private sortAndLimit(results: NodeSearchResult[], limit: number): NodeSearchResult[] {
		return results.sort((a, b) => b.score - a.score).slice(0, limit);
	}

	/**
	 * Validate if a connection type is an AI connection type
	 * @param connectionType - Connection type to validate
	 * @returns True if it's an AI connection type
	 */
	static isAiConnectionType(connectionType: string): boolean {
		return connectionType.startsWith('ai_');
	}

	/**
	 * Get all available AI connection types
	 * @returns Array of AI connection types
	 */
	static getAiConnectionTypes(): NodeConnectionType[] {
		return Object.values(NodeConnectionTypes).filter((type) =>
			NodeSearchEngine.isAiConnectionType(type),
		) as NodeConnectionType[];
	}
}
