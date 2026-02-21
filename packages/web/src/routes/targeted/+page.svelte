<script lang="ts">
	import { api } from '$lib/api/client';
	import type { EstimateResponse } from '$lib/api/client';
	import { algorithm, hardwareTier } from '$lib/stores/settings';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import StrengthMeter from '$lib/components/StrengthMeter.svelte';
	import StrategyBreakdown from '$lib/components/StrategyBreakdown.svelte';
	import DecompositionDisplay from '$lib/components/DecompositionDisplay.svelte';
	import ContextInputs from '$lib/components/ContextInputs.svelte';

	let password = $state('');
	let contextItems = $state<string[]>(['']);
	let result: EstimateResponse | null = $state(null);
	let error = $state('');
	let loading = $state(false);

	async function evaluate() {
		if (!password) return;
		loading = true;
		error = '';
		try {
			const context = contextItems.filter(Boolean);
			result = await api.targeted(password, $algorithm, $hardwareTier, context);
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
		<h1 class="text-2xl font-bold tracking-tight text-heading">Targeted Attack Simulation</h1>
		<p class="mt-1 text-sm text-body">
			Evaluate password strength considering an attacker who knows personal information about the target.
		</p>
	</div>

	<PasswordInput bind:value={password} />
	<ContextInputs bind:items={contextItems} />

	<button
		onclick={evaluate}
		disabled={!password || loading}
		class="w-full rounded-lg border border-accent bg-accent/10 px-4 py-3 font-medium text-accent transition-colors duration-150 hover:bg-accent/20 disabled:opacity-50"
	>
		{loading ? 'Analyzing...' : 'Evaluate with Context'}
	</button>

	{#if error}
		<div class="rounded-lg bg-red-900/20 p-4 text-sm text-red-400">{error}</div>
	{/if}

	{#if result}
		<div class="card space-y-6 rounded-lg border border-edge bg-panel p-6">
			<StrengthMeter
				rating={result.rating}
				ratingLabel={result.rating_label}
				crackTimeDisplay={result.crack_time_display}
			/>

			<p class="text-sm text-body">
				Best attack: <span class="font-medium text-heading">{result.winning_attack}</span>
			</p>

			{#if result.decomposition.length > 0}
				<div>
					<h3 class="mb-2 text-sm font-medium text-body">Decomposition</h3>
					<DecompositionDisplay segments={result.decomposition} />
				</div>
			{/if}

			<div>
				<h3 class="mb-2 text-sm font-medium text-body">Strategies</h3>
				<StrategyBreakdown strategies={result.strategies} />
			</div>
		</div>
	{/if}
</div>
