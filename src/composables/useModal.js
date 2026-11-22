import { ref } from 'vue';

/**
 * Shared composable for managing FullTextModal state across views.
 *
 * @returns {{
 *   isOpen: import('vue').Ref<boolean>,
 *   modalTitle: import('vue').Ref<string>,
 *   modalContent: import('vue').Ref<string>,
 *   modalMeta: import('vue').Ref<Record<string, any>>,
 *   openModal: (title: string, content?: string, meta?: Record<string, any>) => void,
 *   closeModal: () => void
 * }}
 */
export function useModal() {
  const isOpen = ref(false);
  const modalTitle = ref('');
  const modalContent = ref('');
  const modalMeta = ref({});

  function openModal(title, content = '', meta = {}) {
    modalTitle.value = title || '';
    modalContent.value = content || '';
    modalMeta.value = meta && typeof meta === 'object' ? { ...meta } : {};
    isOpen.value = true;
  }

  function closeModal() {
    isOpen.value = false;
    modalTitle.value = '';
    modalContent.value = '';
    modalMeta.value = {};
  }

  return {
    isOpen,
    modalTitle,
    modalContent,
    modalMeta,
    openModal,
    closeModal,
  };
}

export default useModal;
