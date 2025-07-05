<!-- ModalPopup.vue -->
<template>
  <div v-if="visible" class="modal-backdrop">
    <div class="modal-window">
      <h2>{{ title }}</h2>
      <p>{{ message }}</p>
      <input
        v-if="showInput"
        v-model="inputValue"
        placeholder="Enter name..."
        class="modal-input"
      />
      <div class="modal-actions">
        <button @click="confirm">Confirm</button>
        <button @click="cancel">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from "vue";

const props = defineProps({
  visible: Boolean,
  title: String,
  message: String,
  showInput: Boolean,
});

const emit = defineEmits(["confirm", "cancel"]);

const inputValue = ref("");

const confirm = () => {
  emit("confirm", inputValue.value);
};
const cancel = () => {
  emit("cancel");
};
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-window {
  background: white;
  padding: 20px;
  border-radius: 8px;
  min-width: 300px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.modal-input {
  width: 100%;
  padding: 6px;
  margin: 10px 0;
}
</style>
