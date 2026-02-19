<script lang="ts">
	import type { StrategyInfo } from '$lib/api/client';
	import { formatNumber } from '$lib/utils/format';

	let { strategies }: { strategies: Record<string, StrategyInfo> } = $props();

	const sorted = $derived(
		Object.entries(strategies).sort(([, a], [, b]) => {
			const ag = a.guess_number ?? Infinity;
			const bg = b.guess_number ?? Infinity;
			return ag - bg;
		})
	);
</script>

<div class="overflow-x-auto">
	<table class="min-w-full text-sm">
		<thead>
			<tr class="border-b border-gray-200 text-left text-gray-500">
				<th class="py-2 pr-4 font-medium">Strategy</th>
				<th class="py-2 pr-4 font-medium">Guesses</th>
			</tr>
		</thead>
		<tbody>
			{#each sorted as [name, info]}
				<tr class="border-b border-gray-100">
					<td class="py-2 pr-4 font-mono text-xs">{info.attack_name}</td>
					<td class="py-2 pr-4">
						{#if info.guess_number !== null}
							{formatNumber(info.guess_number)}
						{:else}
							<span class="text-gray-400">N/A</span>
						{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
