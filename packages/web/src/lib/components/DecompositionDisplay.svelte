<script lang="ts">
	import type { DecompositionSegment } from '$lib/api/client';

	let { segments }: { segments: DecompositionSegment[] } = $props();

	const typeColors: Record<string, string> = {
		dictionary: '#3b82f6',
		spatial: '#8b5cf6',
		sequence: '#06b6d4',
		date: '#f59e0b',
		repeat: '#ef4444',
		l33t: '#10b981',
		brute_force: '#6b7280',
		mask: '#ec4899'
	};

	function colorFor(type: string): string {
		return typeColors[type] ?? '#6b7280';
	}
</script>

<div class="flex flex-wrap items-center gap-1">
	{#each segments as seg}
		<span
			class="inline-flex flex-col items-center rounded px-2 py-1"
			style="background-color: {colorFor(seg.type)}20; border: 1px solid {colorFor(seg.type)}40"
		>
			<span class="font-mono text-sm font-bold" style="color: {colorFor(seg.type)}"
				>{seg.segment}</span
			>
			<span class="text-[10px] text-gray-500">{seg.type}</span>
		</span>
	{/each}
</div>
