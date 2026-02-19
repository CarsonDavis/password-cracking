<script lang="ts">
	let { value = $bindable(''), placeholder = 'Enter password...' }: { value: string; placeholder?: string } = $props();
	let show = $state(false);
</script>

<div class="relative">
	<input
		type={show ? 'text' : 'password'}
		bind:value
		{placeholder}
		class="w-full rounded-lg border border-gray-300 px-4 py-3 pr-12 font-mono text-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none"
	/>
	<button
		type="button"
		onclick={() => (show = !show)}
		class="absolute top-1/2 right-3 -translate-y-1/2 text-gray-400 hover:text-gray-600"
		aria-label={show ? 'Hide password' : 'Show password'}
	>
		{show ? 'Hide' : 'Show'}
	</button>
</div>
