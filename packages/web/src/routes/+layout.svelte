<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import type { MetadataResponse } from '$lib/api/client';
	import { algorithm, hardwareTier } from '$lib/stores/settings';
	import AlgorithmSelector from '$lib/components/AlgorithmSelector.svelte';
	import HardwareSelector from '$lib/components/HardwareSelector.svelte';

	let { children } = $props();
	let metadata: MetadataResponse | null = $state(null);
	let settingsOpen = $state(false);

	onMount(async () => {
		try {
			metadata = await api.metadata();
		} catch {
			// API not available yet
		}
	});

	const navLinks = [
		{ href: '/', label: 'Evaluate' },
		{ href: '/compare', label: 'Compare' },
		{ href: '/algorithms', label: 'Algorithms' },
		{ href: '/attackers', label: 'Attackers' },
		{ href: '/batch', label: 'Batch' },
		{ href: '/targeted', label: 'Targeted' },
		{ href: '/docs', label: 'API Docs' }
	];
</script>

<div class="min-h-screen bg-gray-50">
	<header class="border-b border-gray-200 bg-white shadow-sm">
		<div class="mx-auto max-w-6xl px-4 py-3">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-6">
					<a href="/" class="text-lg font-bold text-gray-900">Crack-Time</a>
					<nav class="hidden gap-4 md:flex">
						{#each navLinks as link}
							<a href={link.href} class="text-sm text-gray-600 hover:text-gray-900">{link.label}</a>
						{/each}
					</nav>
				</div>
				<button
					onclick={() => (settingsOpen = !settingsOpen)}
					class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
				>
					Settings
				</button>
			</div>

			{#if settingsOpen && metadata}
				<div class="mt-3 grid grid-cols-1 gap-4 border-t border-gray-100 pt-3 md:grid-cols-2">
					<AlgorithmSelector bind:value={$algorithm} options={metadata.algorithms} />
					<HardwareSelector bind:value={$hardwareTier} options={metadata.hardware_tiers} />
				</div>
			{/if}
		</div>
	</header>

	<main class="mx-auto max-w-6xl px-4 py-8">
		{@render children()}
	</main>
</div>
