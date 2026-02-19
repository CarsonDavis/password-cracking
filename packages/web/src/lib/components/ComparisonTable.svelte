<script lang="ts">
	import type { EstimateResponse } from '$lib/api/client';
	import RatingBadge from './RatingBadge.svelte';
	import { formatNumber } from '$lib/utils/format';

	let { results, labelKey = 'password' }: { results: EstimateResponse[]; labelKey?: string } = $props();
</script>

<div class="overflow-x-auto">
	<table class="min-w-full text-sm">
		<thead>
			<tr class="border-b border-gray-200 text-left text-gray-500">
				<th class="py-2 pr-4 font-medium">
					{labelKey === 'password' ? 'Password' : labelKey === 'hash_algorithm' ? 'Algorithm' : 'Hardware'}
				</th>
				<th class="py-2 pr-4 font-medium">Crack Time</th>
				<th class="py-2 pr-4 font-medium">Rating</th>
				<th class="py-2 pr-4 font-medium">Guesses</th>
				<th class="py-2 pr-4 font-medium">Best Attack</th>
			</tr>
		</thead>
		<tbody>
			{#each results as r}
				<tr class="border-b border-gray-100">
					<td class="py-2 pr-4 font-mono">{(r as Record<string, unknown>)[labelKey]}</td>
					<td class="py-2 pr-4">{r.crack_time_display}</td>
					<td class="py-2 pr-4"><RatingBadge rating={r.rating} label={r.rating_label} /></td>
					<td class="py-2 pr-4">{formatNumber(r.guess_number)}</td>
					<td class="py-2 pr-4 text-xs text-gray-600">{r.winning_attack}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
