<template>
  <div>
    <h1>📦 Streamlit Modal Component (Vue)</h1>
    <button @click="openRename">📝 Rename Dataset</button>
    <button @click="openDelete">🗑️ Delete Dataset</button>

    <ModalPopup
      :visible="showModal"
      :title="modalTitle"
      :message="modalMessage"
      :showInput="showInput"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    />
  </div>
</template>

<script setup>
import { ref } from "vue";
import ModalPopup from "./components/ModalPopup.vue";
import { Streamlit } from "streamlit-component-lib";

const showModal = ref(false);
const showInput = ref(false);
const modalTitle = ref("");
const modalMessage = ref("");
const currentAction = ref("");

const openRename = () => {
  modalTitle.value = "Rename Dataset";
  modalMessage.value = "Enter a new name for the dataset:";
  showInput.value = true;
  currentAction.value = "rename";
  showModal.value = true;
};

const openDelete = () => {
  modalTitle.value = "Confirm Deletion";
  modalMessage.value = "Are you sure you want to delete this dataset?";
  showInput.value = false;
  currentAction.value = "delete";
  showModal.value = true;
};

const handleConfirm = (inputValue) => {
  Streamlit.setComponentValue({
    action: currentAction.value,
    value: inputValue,
  });
  showModal.value = false;
};

const handleCancel = () => {
  Streamlit.setComponentValue({
    action: "cancel",
  });
  showModal.value = false;
};
</script>
