const STORAGE_KEY = "validador-atendimento-whatsapp-v1";

const state = {
  meta: {
    auditName: "",
    channel: "",
    auditor: "",
    auditDate: new Date().toISOString().slice(0, 10),
  },
  tests: [],
  editingId: null,
};

const elements = {
  auditName: document.querySelector("#auditName"),
  channel: document.querySelector("#channel"),
  auditor: document.querySelector("#auditor"),
  auditDate: document.querySelector("#auditDate"),
  testForm: document.querySelector("#testForm"),
  testTitle: document.querySelector("#testTitle"),
  scenario: document.querySelector("#scenario"),
  expected: document.querySelector("#expected"),
  notes: document.querySelector("#notes"),
  testsList: document.querySelector("#testsList"),
  emptyState: document.querySelector("#emptyState"),
  template: document.querySelector("#testItemTemplate"),
  totalTests: document.querySelector("#totalTests"),
  conformTests: document.querySelector("#conformTests"),
  nonConformTests: document.querySelector("#nonConformTests"),
  conformityRate: document.querySelector("#conformityRate"),
  reportMeta: document.querySelector("#reportMeta"),
  printButton: document.querySelector("#printButton"),
  clearAllButton: document.querySelector("#clearAllButton"),
  exportCsvButton: document.querySelector("#exportCsvButton"),
};

function loadState() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) return;

  try {
    const parsed = JSON.parse(saved);
    state.meta = { ...state.meta, ...parsed.meta };
    state.tests = Array.isArray(parsed.tests) ? parsed.tests : [];
  } catch {
    localStorage.removeItem(STORAGE_KEY);
  }
}

function saveState() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ meta: state.meta, tests: state.tests })
  );
}

function bindMetaFields() {
  setMetaFieldValues();

  Object.keys(state.meta).forEach((key) => {
    const field = elements[key];
    field.addEventListener("input", () => {
      state.meta[key] = field.value;
      saveState();
      renderMeta();
    });
  });
}

function setMetaFieldValues() {
  Object.keys(state.meta).forEach((key) => {
    elements[key].value = state.meta[key];
  });
}

function getSelectedStatus() {
  return new FormData(elements.testForm).get("status") || "conforme";
}

function generateId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function setSelectedStatus(status) {
  const option = elements.testForm.querySelector(`[name="status"][value="${status}"]`);
  if (option) option.checked = true;
}

function statusLabel(status) {
  const labels = {
    conforme: "Conforme",
    "nao-conforme": "Não conforme",
    pendente: "Pendente",
  };

  return labels[status] || "Pendente";
}

function calculateSummary() {
  const total = state.tests.length;
  const conform = state.tests.filter((test) => test.status === "conforme").length;
  const nonConform = state.tests.filter((test) => test.status === "nao-conforme").length;
  const evaluated = conform + nonConform;
  const rate = evaluated ? Math.round((conform / evaluated) * 100) : 0;

  return { total, conform, nonConform, rate };
}

function renderSummary() {
  const summary = calculateSummary();
  elements.totalTests.textContent = summary.total;
  elements.conformTests.textContent = summary.conform;
  elements.nonConformTests.textContent = summary.nonConform;
  elements.conformityRate.textContent = `${summary.rate}%`;
}

function renderMeta() {
  const items = [
    ["Bateria", state.meta.auditName || "Não informado"],
    ["Canal", state.meta.channel || "Não informado"],
    ["Responsável", state.meta.auditor || "Não informado"],
    ["Data", state.meta.auditDate || "Não informado"],
  ];

  elements.reportMeta.innerHTML = "";
  items.forEach(([label, value]) => {
    const wrapper = document.createElement("div");
    const labelElement = document.createElement("span");
    const valueElement = document.createElement("strong");

    labelElement.textContent = label;
    valueElement.textContent = value;
    wrapper.append(labelElement, valueElement);
    elements.reportMeta.appendChild(wrapper);
  });
}

function fallbackText(value) {
  return value?.trim() || "Não informado.";
}

function renderTests() {
  elements.testsList.innerHTML = "";
  elements.emptyState.hidden = state.tests.length > 0;

  state.tests.forEach((test, index) => {
    const item = elements.template.content.firstElementChild.cloneNode(true);
    const badge = item.querySelector(".status-badge");

    item.querySelector(".test-index").textContent = `Teste ${index + 1}`;
    item.querySelector("h3").textContent = test.title;
    item.querySelector(".scenario-text").textContent = fallbackText(test.scenario);
    item.querySelector(".expected-text").textContent = fallbackText(test.expected);
    item.querySelector(".notes-text").textContent = fallbackText(test.notes);
    badge.textContent = statusLabel(test.status);
    badge.classList.add(test.status);

    item.querySelector(".edit-button").addEventListener("click", () => editTest(test.id));
    item.querySelector(".delete-button").addEventListener("click", () => deleteTest(test.id));
    elements.testsList.appendChild(item);
  });
}

function render() {
  renderMeta();
  renderSummary();
  renderTests();
}

function resetForm() {
  elements.testForm.reset();
  setSelectedStatus("conforme");
  state.editingId = null;
  elements.testForm.querySelector("[type='submit']").textContent = "Adicionar teste";
}

function handleSubmit(event) {
  event.preventDefault();

  const payload = {
    id: state.editingId || generateId(),
    title: elements.testTitle.value.trim(),
    scenario: elements.scenario.value.trim(),
    expected: elements.expected.value.trim(),
    notes: elements.notes.value.trim(),
    status: getSelectedStatus(),
    createdAt: new Date().toISOString(),
  };

  if (!payload.title) return;

  if (state.editingId) {
    state.tests = state.tests.map((test) =>
      test.id === state.editingId ? { ...test, ...payload } : test
    );
  } else {
    state.tests.unshift(payload);
  }

  saveState();
  render();
  resetForm();
}

function editTest(id) {
  const test = state.tests.find((item) => item.id === id);
  if (!test) return;

  state.editingId = id;
  elements.testTitle.value = test.title;
  elements.scenario.value = test.scenario;
  elements.expected.value = test.expected;
  elements.notes.value = test.notes;
  setSelectedStatus(test.status);
  elements.testForm.querySelector("[type='submit']").textContent = "Salvar alteração";
  elements.testTitle.focus();
}

function deleteTest(id) {
  const test = state.tests.find((item) => item.id === id);
  if (!test) return;

  const confirmed = window.confirm(`Excluir o teste "${test.title}"?`);
  if (!confirmed) return;

  state.tests = state.tests.filter((item) => item.id !== id);
  saveState();
  render();
}

function clearAll() {
  const confirmed = window.confirm("Limpar a bateria e todos os testes cadastrados?");
  if (!confirmed) return;

  state.meta = {
    auditName: "",
    channel: "",
    auditor: "",
    auditDate: new Date().toISOString().slice(0, 10),
  };
  state.tests = [];
  saveState();
  setMetaFieldValues();
  resetForm();
  render();
}

function escapeCsv(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function exportCsv() {
  const summary = calculateSummary();
  const rows = [
    ["Bateria", state.meta.auditName],
    ["Canal", state.meta.channel],
    ["Responsavel", state.meta.auditor],
    ["Data", state.meta.auditDate],
    ["Total", summary.total],
    ["Conformes", summary.conform],
    ["Nao conformes", summary.nonConform],
    ["Percentual conformidade", `${summary.rate}%`],
    [],
    ["Teste", "Status", "Cenario", "Esperado", "Observacoes"],
    ...state.tests.map((test) => [
      test.title,
      statusLabel(test.status),
      test.scenario,
      test.expected,
      test.notes,
    ]),
  ];

  const csv = rows.map((row) => row.map(escapeCsv).join(";")).join("\n");
  const blob = new Blob([`\ufeff${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `relatorio-testes-whatsapp-${state.meta.auditDate || "sem-data"}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function init() {
  loadState();
  bindMetaFields();
  render();

  elements.testForm.addEventListener("submit", handleSubmit);
  elements.printButton.addEventListener("click", () => window.print());
  elements.clearAllButton.addEventListener("click", clearAll);
  elements.exportCsvButton.addEventListener("click", exportCsv);
}

init();
