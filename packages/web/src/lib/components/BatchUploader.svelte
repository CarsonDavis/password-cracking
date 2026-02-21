<script lang="ts">
	let { onUpload }: { onUpload: (passwords: string[]) => void } = $props();
	let textarea = $state('');

	function handleFile(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		const reader = new FileReader();
		reader.onload = () => {
			textarea = reader.result as string;
		};
		reader.readAsText(file);
	}

	function submit() {
		const passwords = textarea
			.split('\n')
			.map((l) => l.trim())
			.filter(Boolean);
		if (passwords.length > 0) {
			onUpload(passwords);
		}
	}
</script>

<div class="space-y-3">
	<div>
		<p class="block text-sm font-medium text-body">Upload file or paste passwords (one per line)</p>
		<input
			type="file"
			accept=".txt,.csv"
			onchange={handleFile}
			class="mt-1 block text-sm text-body file:mr-4 file:rounded-md file:border file:border-edge file:bg-panel file:px-4 file:py-2 file:text-sm file:font-medium file:text-accent file:transition-colors file:duration-150 hover:file:border-accent"
		/>
	</div>
	<textarea
		bind:value={textarea}
		rows={6}
		placeholder="password123&#10;hunter2&#10;Tr0ub4dor&3"
		class="w-full rounded-lg border border-edge bg-input px-3 py-2 font-mono text-sm text-heading placeholder-body focus:border-accent focus:ring-1 focus:ring-accent/30 focus:outline-none"
	></textarea>
	<button
		onclick={submit}
		disabled={!textarea.trim()}
		class="rounded-md border border-accent bg-accent/10 px-4 py-2 text-sm font-medium text-accent transition-colors duration-150 hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-50"
	>
		Analyze Batch
	</button>
</div>
