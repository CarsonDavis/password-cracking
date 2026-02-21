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

<div class="min-h-screen bg-canvas">
	<header class="border-b border-edge bg-panel">
		<div class="mx-auto max-w-6xl px-4 py-3">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-6">
					<a href="/" class="text-lg font-bold text-heading tracking-tight">Crack-Time</a>
					<nav class="hidden gap-4 md:flex">
						{#each navLinks as link}
							<a
								href={link.href}
								class="text-sm text-body transition-colors duration-150 hover:text-accent"
							>
								{link.label}
							</a>
						{/each}
					</nav>
				</div>
				<button
					onclick={() => (settingsOpen = !settingsOpen)}
					class="rounded-md border border-edge px-3 py-1.5 text-sm text-body transition-colors duration-150 hover:border-accent hover:text-accent"
				>
					Settings
				</button>
			</div>

			{#if settingsOpen && metadata}
				<div class="mt-3 grid grid-cols-1 gap-4 border-t border-edge pt-3 md:grid-cols-2">
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
