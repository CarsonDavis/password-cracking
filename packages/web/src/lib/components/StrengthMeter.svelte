<script lang="ts">
	import { RATING_COLORS } from '$lib/utils/format';

	let { rating, ratingLabel, crackTimeDisplay }: { rating: number; ratingLabel: string; crackTimeDisplay: string } = $props();

	const widthPercent = $derived(((rating + 1) / 5) * 100);
	const color = $derived(RATING_COLORS[rating] ?? '#6b7280');
</script>

<div class="space-y-2">
	<div class="flex items-center justify-between">
		<span class="text-sm font-medium" style="color: {color}">{ratingLabel} ({rating}/4)</span>
		<span class="text-sm text-body">~{crackTimeDisplay}</span>
	</div>
	<div class="h-3 w-full overflow-hidden rounded-full bg-edge">
		<div
			class="h-full rounded-full transition-all duration-500"
			style="width: {widthPercent}%; background-color: {color}"
		></div>
	</div>
</div>
