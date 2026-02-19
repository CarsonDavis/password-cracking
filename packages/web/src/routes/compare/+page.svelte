<script lang="ts">
	import { api } from '$lib/api/client';
	import type { EstimateResponse } from '$lib/api/client';
	import { algorithm, hardwareTier } from '$lib/stores/settings';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import ComparisonTable from '$lib/components/ComparisonTable.svelte';
	import CrackTimeChart from '$lib/components/CrackTimeChart.svelte';

	let passwords = $state(['', '']);
	let results: EstimateResponse[] = $state([]);
	let error = $state('');
	let loading = $state(false);

	function addField() {
		passwords = [...passwords, ''];
	}

	function removeField(i: number) {
		passwords = passwords.filter((_, idx) => idx !== i);
	}

	function updatePassword(i: number, value: string) {
		passwords = passwords.map((p, idx) => (idx === i ? value : p));
	}

	async function compare() {
		const filled = passwords.filter(Boolean);
		if (filled.length < 2) {
			error = 'Enter at least 2 passwords to compare';
			return;
		}
		loading = true;
		error = '';
		try {
			results = await api.comparePasswords(filled, $algorithm, $hardwareTier);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Request failed';
			results = [];
		} finally {
			loading = false;
		}
	}
</script>

<div class="mx-auto max-w-3xl space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-900">Compare Passwords</h1>
		<p class="mt-1 text-sm text-gray-500">See how different passwords stack up side by side.</p>
	</div>

	<div class="space-y-3">
		{#each passwords as pw, i}
			<div class="flex gap-2">
				<div class="flex-1">
					<PasswordInput
						value={pw}
						placeholder="Password {i + 1}"
						oninput={(e: Event) => updatePassword(i, (e.target as HTMLInputElement).value)}
					/>
				</div>
				{#if passwords.length > 2}
					<button onclick={() => removeField(i)} class="text-red-500 hover:text-red-700">&times;</button>
				{/if}
			</div>
		{/each}
		<button onclick={addField} class="text-sm text-blue-600 hover:text-blue-800">+ Add password</button>
	</div>

	<button
		onclick={compare}
		disabled={loading}
		class="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
	>
		{loading ? 'Comparing...' : 'Compare'}
	</button>

	{#if error}
		<div class="rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
	{/if}

	{#if results.length > 0}
		<div class="space-y-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
			<CrackTimeChart {results} labelKey="password" />
			<ComparisonTable {results} labelKey="password" />
		</div>
	{/if}
</div>
