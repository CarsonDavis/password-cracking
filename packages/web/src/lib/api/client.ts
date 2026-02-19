/**
 * API client for the crack-time backend.
 * Calls go through the Vite proxy (/api -> localhost:8000).
 */

export interface DecompositionSegment {
	segment: string;
	type: string;
	guesses: number;
	i: number;
	j: number;
}

export interface StrategyInfo {
	guess_number: number | null;
	attack_name: string;
	details: Record<string, unknown>;
}

export interface EstimateResponse {
	password: string;
	hash_algorithm: string;
	hardware_tier: string;
	effective_hash_rate: number;
	guess_number: number | null;
	crack_time_seconds: number | null;
	crack_time_display: string;
	rating: number;
	rating_label: string;
	winning_attack: string;
	strategies: Record<string, StrategyInfo>;
	decomposition: DecompositionSegment[];
}

export interface BatchPasswordResult {
	password: string;
	crack_time_seconds: number | null;
	crack_time_display: string;
	rating: number;
	rating_label: string;
	winning_attack: string;
	guess_number: number | null;
}

export interface BatchSummary {
	median_crack_time_seconds: number;
	rating_distribution: Record<number, number>;
	winning_attack_distribution: Record<string, number>;
}

export interface BatchResponse {
	total_passwords: number;
	summary: BatchSummary;
	passwords: BatchPasswordResult[];
}

export interface AlgorithmOption {
	name: string;
	rate: number;
}

export interface TierOption {
	name: string;
	description: string;
	multiplier: number;
}

export interface MetadataResponse {
	algorithms: AlgorithmOption[];
	hardware_tiers: TierOption[];
}

async function post<T>(url: string, body: unknown): Promise<T> {
	const resp = await fetch(url, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({ detail: resp.statusText }));
		throw new Error(err.detail || resp.statusText);
	}
	return resp.json();
}

async function get<T>(url: string): Promise<T> {
	const resp = await fetch(url);
	if (!resp.ok) {
		throw new Error(resp.statusText);
	}
	return resp.json();
}

export const api = {
	estimate(password: string, algorithm: string, hardware_tier: string) {
		return post<EstimateResponse>('/api/estimate', { password, algorithm, hardware_tier });
	},

	batch(passwords: string[], algorithm: string, hardware_tier: string) {
		return post<BatchResponse>('/api/batch', { passwords, algorithm, hardware_tier });
	},

	comparePasswords(passwords: string[], algorithm: string, hardware_tier: string) {
		return post<EstimateResponse[]>('/api/compare/passwords', {
			passwords,
			algorithm,
			hardware_tier
		});
	},

	compareAlgorithms(password: string, algorithms: string[], hardware_tier: string) {
		return post<EstimateResponse[]>('/api/compare/algorithms', {
			password,
			algorithms,
			hardware_tier
		});
	},

	compareAttackers(password: string, algorithm: string, hardware_tiers: string[]) {
		return post<EstimateResponse[]>('/api/compare/attackers', {
			password,
			algorithm,
			hardware_tiers
		});
	},

	metadata() {
		return get<MetadataResponse>('/api/metadata');
	},

	targeted(
		password: string,
		algorithm: string,
		hardware_tier: string,
		context: string[]
	) {
		return post<EstimateResponse>('/api/targeted', {
			password,
			algorithm,
			hardware_tier,
			context
		});
	}
};
