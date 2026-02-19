<script lang="ts">
	import { RATING_COLORS, RATING_BG_COLORS } from '$lib/utils/format';

	let { rating, label }: { rating: number; label: string } = $props();
</script>

<span
	class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
	style="color: {RATING_COLORS[rating]}; background-color: {RATING_BG_COLORS[rating]}"
>
	{label}
</span>
