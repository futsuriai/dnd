<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="modal-overlay"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="title ? titleId : undefined"
      :aria-label="title ? undefined : 'Details dialog'"
      @click.self="closeModal"
    >
      <div class="modal-content" ref="modalRef">
        <button
          type="button"
          class="close-button"
          aria-label="Close modal"
          @click="closeModal"
        >
          &times;
        </button>
        <h2 v-if="title" :id="titleId" class="modal-title">{{ title }}</h2>

        <!-- Conditionally display image, loading indicator, or text -->
        <div v-if="imageUrl" class="modal-image-container">
          <img :src="imageUrl" :alt="title || 'Modal Image'" class="modal-image" />
        </div>
        <div v-else-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading...</p>
        </div>
        <div
          v-else
          class="modal-body"
          :class="contentClass"
          v-html="renderedContent"
          @click="handleContentClick"
        ></div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, watch, onBeforeUnmount, useId } from 'vue';
import { useRouter } from 'vue-router';
import { marked } from 'marked';
import { resolveEntityByNameOrId } from '@/store/worldData.js';

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  text: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '',
  },
  imageUrl: {
    type: String,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  contentClass: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['close']);
const router = useRouter();
const titleId = `modal-title-${useId()}`;

let previousBodyOverflow = '';
let isScrollLocked = false;

function lockBodyScroll() {
  if (typeof document === 'undefined' || isScrollLocked) return;
  previousBodyOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  isScrollLocked = true;
}

function unlockBodyScroll() {
  if (typeof document === 'undefined' || !isScrollLocked) return;
  document.body.style.overflow = previousBodyOverflow;
  isScrollLocked = false;
}

function closeModal() {
  emit('close');
}

function handleKeydown(event) {
  if (event.key === 'Escape' && props.visible) {
    event.preventDefault();
    closeModal();
  }
}

watch(
  () => props.visible,
  (isVisible) => {
    if (typeof window === 'undefined') return;
    if (isVisible) {
      lockBodyScroll();
      window.addEventListener('keydown', handleKeydown);
    } else {
      unlockBodyScroll();
      window.removeEventListener('keydown', handleKeydown);
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  unlockBodyScroll();
  if (typeof window !== 'undefined') {
    window.removeEventListener('keydown', handleKeydown);
  }
});

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function extractWikiLabel(rawInner, resolved) {
  const pipeIdx = rawInner.indexOf('|');
  if (pipeIdx !== -1) {
    const alias = rawInner.slice(pipeIdx + 1).trim();
    if (alias) return alias;
  }
  const hashIdx = rawInner.indexOf('#');
  if (hashIdx !== -1) {
    const anchorText = rawInner.slice(hashIdx + 1).trim();
    if (anchorText) return anchorText;
  }
  const target = rawInner.includes('/') ? rawInner.split('/').pop().trim() : rawInner.trim();
  return target || (resolved ? resolved.name : rawInner);
}

function renderMarkdown(rawText) {
  if (!rawText) return '';

  const linkedText = rawText.replace(/\[\[([^\]]+)\]\]/g, (_match, rawInner) => {
    const resolved = resolveEntityByNameOrId(rawInner);
    const displayLabel = extractWikiLabel(rawInner, resolved);
    if (resolved && resolved.route) {
      const safeRoute = escapeHtml(resolved.route);
      return `<a href="#${safeRoute}" class="wikilink" data-route="${safeRoute}">${escapeHtml(displayLabel)}</a>`;
    }
    return `<span class="wikilink-unresolved">${escapeHtml(displayLabel)}</span>`;
  });

  const html = marked.parse(linkedText);
  return html.replace(/<table([\s\S]*?)<\/table>/g, '<div class="table-scroll-wrapper"><table$1</table></div>');
}

const renderedContent = computed(() => {
  if (!props.text) return '';
  if (props.contentClass === 'transcript-content') {
    return props.text;
  }
  return renderMarkdown(props.text);
});

function handleContentClick(event) {
  const link = event.target.closest('a');
  if (!link) return;

  const dataRoute = link.getAttribute('data-route');
  if (dataRoute) {
    event.preventDefault();
    closeModal();
    router.push(dataRoute);
    return;
  }

  const href = link.getAttribute('href') || '';
  if (href.startsWith('#/')) {
    event.preventDefault();
    closeModal();
    router.push(href.slice(1));
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.78);
  backdrop-filter: blur(2px);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  box-sizing: border-box;
  z-index: 1000;
}

.modal-content {
  background-color: var(--color-background);
  padding: 2rem;
  border-radius: 8px;
  width: min(900px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.close-button {
  position: absolute;
  top: 0.9rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.8rem;
  color: var(--color-text-muted);
  cursor: pointer;
  line-height: 1;
  padding: 0.2rem 0.5rem;
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text);
}

.modal-body {
  margin-top: 0;
  line-height: 1.7;
  overflow-y: auto;
  flex-grow: 1;
}

/* Scrollable wrapper for wide Markdown tables */
.modal-body :deep(.table-scroll-wrapper) {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 1em 0;
  border-radius: 6px;
}

.modal-body :deep(table) {
  width: 100%;
  min-width: 520px;
  border-collapse: collapse;
  margin: 0;
  font-size: 0.9em;
  font-family: var(--font-main);
}

.modal-body :deep(th),
.modal-body :deep(td) {
  border: 1px solid var(--border-color);
  padding: 0.55em 1.25em 0.55em 0.75em;
  text-align: left;
}

.modal-body :deep(th) {
  background-color: var(--color-background-soft);
  font-weight: bold;
  color: var(--color-heading);
}

.modal-body :deep(tr:nth-child(even)) {
  background-color: var(--color-background-mute);
}

/* Links generated by markdown & WikiLinks */
.modal-body :deep(a) {
  color: var(--color-link);
  text-decoration: none;
  font-weight: 600;
  border-bottom: 1px dotted rgba(91, 176, 207, 0.45);
}

.modal-body :deep(a:hover) {
  color: var(--color-link-hover);
  border-bottom-color: var(--color-link-hover);
  text-decoration: none;
}

.modal-body :deep(.wikilink-unresolved) {
  color: var(--color-text-muted);
  font-style: italic;
}

.modal-body :deep(p) {
  margin-bottom: 1em;
}

.modal-body :deep(blockquote) {
  margin: 1rem 0;
  padding: 0.75rem 1rem;
  border-left: 3px solid var(--color-primary);
  background: var(--color-background-soft);
  border-radius: 0 6px 6px 0;
  font-style: italic;
}

.modal-body :deep(h1),
.modal-body :deep(h2),
.modal-body :deep(h3) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  color: var(--color-primary);
}

.modal-body :deep(ul),
.modal-body :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.modal-body :deep(li) {
  margin-bottom: 0.45rem;
}

.modal-title {
  font-family: var(--font-display);
  color: var(--color-primary);
  margin: 0 2.5rem 1rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
  font-size: 1.55rem;
  line-height: 1.3;
}

.modal-image-container {
  text-align: center;
  padding: 1rem 0;
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-image {
  max-width: 100%;
  max-height: 75vh;
  height: auto;
  display: block;
  margin: 0 auto;
  border-radius: 6px;
}

/* Loading styles */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  height: 200px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  border-top-color: var(--color-primary);
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Transcript-specific styles */
.modal-body.transcript-content {
  font-family: var(--font-main);
  font-size: 0.9rem;
  line-height: 1.5;
  padding: 0;
}

.modal-body.transcript-content :deep(.transcript-line) {
  display: flex;
  align-items: flex-start;
  padding: 0.3em 0.5em;
  border-radius: 4px;
  gap: 0.5em;
  transition: background-color 0.15s;
}

.modal-body.transcript-content :deep(.transcript-line:hover) {
  background-color: var(--color-background-soft);
}

.modal-body.transcript-content :deep(.transcript-line.new-speaker) {
  margin-top: 0.6em;
  border-top: 1px solid var(--border-color);
  padding-top: 0.6em;
}

.modal-body.transcript-content :deep(.transcript-avatar) {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--border-color);
}

.modal-body.transcript-content :deep(.transcript-avatar-placeholder) {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-background-mute);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7em;
  font-weight: bold;
  color: var(--text-muted);
  flex-shrink: 0;
  border: 1px solid var(--border-color);
}

.modal-body.transcript-content :deep(.transcript-timestamp) {
  color: var(--text-muted);
  font-size: 0.75em;
  font-family: var(--font-mono);
  opacity: 0.7;
  flex-shrink: 0;
  min-width: 55px;
}

.modal-body.transcript-content :deep(.transcript-speaker) {
  font-weight: 600;
  flex-shrink: 0;
  min-width: 80px;
}

.modal-body.transcript-content :deep(.transcript-speaker.speaker-gm) {
  color: #e6a23c;
}

.modal-body.transcript-content :deep(.transcript-speaker.speaker-nyx) {
  color: #9a8fbd;
}

.modal-body.transcript-content :deep(.transcript-speaker.speaker-ellara) {
  color: #d4a855;
}

.modal-body.transcript-content :deep(.transcript-speaker.speaker-berridin) {
  color: #c49a6c;
}

.modal-body.transcript-content :deep(.transcript-speaker.speaker-ysidor) {
  color: #7ba3c4;
}

.modal-body.transcript-content :deep(.transcript-speaker.speaker-tsinyra) {
  color: #7cb587;
}

.modal-body.transcript-content :deep(.transcript-speaker.speaker-witty) {
  color: #b08dc9;
}

.modal-body.transcript-content :deep(.transcript-speaker.speaker-unknown) {
  color: var(--color-text-muted);
}

.modal-body.transcript-content :deep(.transcript-text) {
  color: var(--color-text);
  flex: 1;
}

.modal-body.transcript-content :deep(.transcript-line.transcript-plain) {
  color: var(--text-muted);
  font-style: italic;
  padding-left: 2em;
}

@media (max-width: 600px) {
  .modal-content {
    padding: 1.25rem;
  }

  .modal-title {
    font-size: 1.3rem;
  }
}
</style>
