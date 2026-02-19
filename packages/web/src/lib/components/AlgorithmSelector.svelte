<script lang="ts">
	import type { AlgorithmOption } from '$lib/api/client';
	import { algorithmLabel, formatRate } from '$lib/utils/format';

	let {
		value = $bindable('bcrypt_cost12'),
		options = [] as AlgorithmOption[]
	}: { value: string; options?: AlgorithmOption[] } = $props();
</script>

<label class="block text-sm font-medium text-gray-700">
	Hash Algorithm
	<select
		bind:value
		class="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
	>
		{#each options as opt}
			<option value={opt.name}>{algorithmLabel(opt.name)} ({formatRate(opt.rate)})</option>
		{/each}
	</select>
</label>
