<script lang="ts">
	import { api } from '$lib/api/client';
	import type { EstimateResponse } from '$lib/api/client';
	import { algorithm, hardwareTier } from '$lib/stores/settings';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import StrengthMeter from '$lib/components/StrengthMeter.svelte';
	import StrategyBreakdown from '$lib/components/StrategyBreakdown.svelte';
	import DecompositionDisplay from '$lib/components/DecompositionDisplay.svelte';

	let password = $state('');
	let result: EstimateResponse | null = $state(null);
	let error = $state('');
	let loading = $state(false);

	async function evaluate() {
		if (!password) return;
		loading = true;
		error = '';
		try {
			result = await api.estimate(password, $algorithm, $hardwareTier);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Request failed';
			result = null;
		} finally {
			loading = false;
		}
	}
</script>

<div class="mx-auto max-w-2xl space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-900">Password Strength Evaluator</h1>
		<p class="mt-1 text-sm text-gray-500">
			Estimate how long it would take to crack a password using analytical attack models.
		</p>
	</div>

	<div class="space-y-4">
		<PasswordInput bind:value={password} />

		<button
			onclick={evaluate}
			disabled={!password || loading}
			class="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
		>
			{loading ? 'Analyzing...' : 'Evaluate'}
		</button>
	</div>

	{#if error}
		<div class="rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
	{/if}

	{#if result}
		<div class="space-y-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
			<StrengthMeter
				rating={result.rating}
				ratingLabel={result.rating_label}
				crackTimeDisplay={result.crack_time_display}
			/>

			<div class="space-y-1">
				<p class="text-sm text-gray-500">
					Best attack: <span class="font-medium text-gray-700">{result.winning_attack}</span>
				</p>
				<p class="text-sm text-gray-500">
					Hash rate: <span class="font-medium text-gray-700">{result.effective_hash_rate.toLocaleString()} H/s</span>
				</p>
			</div>

			{#if result.decomposition.length > 0}
				<div>
					<h3 class="mb-2 text-sm font-medium text-gray-700">Password Decomposition</h3>
					<DecompositionDisplay segments={result.decomposition} />
				</div>
			{/if}

			<div>
				<h3 class="mb-2 text-sm font-medium text-gray-700">Attack Strategies</h3>
				<StrategyBreakdown strategies={result.strategies} />
			</div>
		</div>
	{/if}
</div>
