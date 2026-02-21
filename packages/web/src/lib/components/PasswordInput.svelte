<script lang="ts">
	let { value = $bindable(''), placeholder = 'Enter password...' }: { value: string; placeholder?: string } = $props();
	let show = $state(false);
</script>

<div class="relative">
	<input
		type={show ? 'text' : 'password'}
		bind:value
		{placeholder}
		class="w-full rounded-lg border border-edge bg-input px-4 py-3 pr-12 font-mono text-lg text-heading placeholder-body focus:border-accent focus:ring-2 focus:ring-accent/30 focus:outline-none"
	/>
	<button
		type="button"
		onclick={() => (show = !show)}
		class="absolute top-1/2 right-3 -translate-y-1/2 text-body transition-colors duration-150 hover:text-accent"
		aria-label={show ? 'Hide password' : 'Show password'}
	>
		{show ? 'Hide' : 'Show'}
	</button>
</div>
