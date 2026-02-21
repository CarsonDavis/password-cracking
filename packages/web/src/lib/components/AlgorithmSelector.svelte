<script lang="ts">
	import type { AlgorithmOption } from '$lib/api/client';
	import { algorithmLabel, formatRate } from '$lib/utils/format';

	let {
		value = $bindable('bcrypt_cost12'),
		options = [] as AlgorithmOption[]
	}: { value: string; options?: AlgorithmOption[] } = $props();
</script>

<label class="block text-sm font-medium text-body">
	Hash Algorithm
	<select
		bind:value
		class="mt-1 block w-full rounded-md border border-edge bg-input px-3 py-2 text-sm text-heading focus:border-accent focus:ring-1 focus:ring-accent/30 focus:outline-none"
	>
		{#each options as opt}
			<option value={opt.name}>{algorithmLabel(opt.name)} ({formatRate(opt.rate)})</option>
		{/each}
	</select>
</label>
