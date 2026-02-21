<script lang="ts">
	let { items = $bindable([]) }: { items: string[] } = $props();

	function add() {
		items = [...items, ''];
	}

	function remove(index: number) {
		items = items.filter((_, i) => i !== index);
	}

	function update(index: number, value: string) {
		items = items.map((item, i) => (i === index ? value : item));
	}
</script>

<div class="space-y-2">
	<p class="block text-sm font-medium text-body">Personal Context (names, dates, pets, etc.)</p>
	{#each items as item, i}
		<div class="flex gap-2">
			<input
				type="text"
				value={item}
				oninput={(e) => update(i, (e.target as HTMLInputElement).value)}
				placeholder="e.g., john, 1990, fluffy"
				class="flex-1 rounded-md border border-edge bg-input px-3 py-1.5 text-sm text-heading placeholder-body focus:border-accent focus:ring-1 focus:ring-accent/30 focus:outline-none"
			/>
			<button
				onclick={() => remove(i)}
				class="rounded-md px-2 text-red-400 transition-colors duration-150 hover:bg-red-900/30"
				aria-label="Remove"
			>
				&times;
			</button>
		</div>
	{/each}
	<button
		onclick={add}
		class="text-sm text-accent transition-colors duration-150 hover:text-accent-hover"
	>
		+ Add context item
	</button>
</div>
