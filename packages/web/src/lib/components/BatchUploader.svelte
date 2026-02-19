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
		<p class="block text-sm font-medium text-gray-700">Upload file or paste passwords (one per line)</p>
		<input
			type="file"
			accept=".txt,.csv"
			onchange={handleFile}
			class="mt-1 block text-sm text-gray-500 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-blue-700 hover:file:bg-blue-100"
		/>
	</div>
	<textarea
		bind:value={textarea}
		rows={6}
		placeholder="password123&#10;hunter2&#10;Tr0ub4dor&3"
		class="w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
	></textarea>
	<button
		onclick={submit}
		disabled={!textarea.trim()}
		class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
	>
		Analyze Batch
	</button>
</div>
