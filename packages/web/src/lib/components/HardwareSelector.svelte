<script lang="ts">
	import type { TierOption } from '$lib/api/client';
	import { tierLabel } from '$lib/utils/format';

	let {
		value = $bindable('consumer'),
		options = [] as TierOption[]
	}: { value: string; options?: TierOption[] } = $props();
</script>

<label class="block text-sm font-medium text-gray-700">
	Hardware Tier
	<select
		bind:value
		class="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
	>
		{#each options as opt}
			<option value={opt.name}>{tierLabel(opt.name)} — {opt.description} ({opt.multiplier}x)</option>
		{/each}
	</select>
</label>
