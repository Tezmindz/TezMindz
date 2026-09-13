/**
 * curriculum_dependent_selects.js
 * Handles responsive, cascading dropdowns in Django Admin for Concept and Game.
 * Features:
 * - Empty default states
 * - Downstream disabling until upstream is chosen
 * - Loading indicator
 * - Automatic reset of stale selections when upstream changes
 * - Pre-population on EDIT forms
 */
(function() {
  document.addEventListener('DOMContentLoaded', function() {
    const gradeSelect = document.getElementById('id_grade');
    const subjectSelect = document.getElementById('id_subject');
    const topicSelect = document.getElementById('id_topic');     // on ConceptAdminForm
    const chapterSelect = document.getElementById('id_chapter'); // on GameAdminForm
    const conceptSelect = document.getElementById('id_concept'); // on GameAdminForm

    if (!gradeSelect) return;

    // Helper to clear and disable a select
    function resetSelect(selectEl, defaultText) {
      if (!selectEl) return;
      selectEl.innerHTML = `<option value="">${defaultText}</option>`;
      selectEl.disabled = true;
    }

    // Helper to populate a select
    function populateSelect(selectEl, items, selectedVal, defaultText, textKey = 'name') {
      if (!selectEl) return;
      let html = `<option value="">${defaultText}</option>`;
      items.forEach(item => {
        const isSelected = selectedVal && String(item.id) === String(selectedVal);
        html += `<option value="${item.id}" ${isSelected ? 'selected' : ''}>${item[textKey] || item.title || item.name}</option>`;
      });
      selectEl.innerHTML = html;
      selectEl.disabled = items.length === 0;
    }

    // Capture initial values for edit mode
    const initialGradeId = gradeSelect.value;
    const initialSubjectId = subjectSelect ? subjectSelect.value : null;
    const initialChapterId = (topicSelect ? topicSelect.value : (chapterSelect ? chapterSelect.value : null));
    const initialConceptId = conceptSelect ? conceptSelect.value : null;

    // Fetch subjects for grade
    async function loadSubjects(gradeId, preserveSelected = null) {
      if (!subjectSelect) return;
      if (!gradeId) {
        resetSelect(subjectSelect, '--- Select Grade first ---');
        if (topicSelect) resetSelect(topicSelect, '--- Select Subject first ---');
        if (chapterSelect) resetSelect(chapterSelect, '--- Select Subject first ---');
        if (conceptSelect) resetSelect(conceptSelect, '--- Select Chapter first ---');
        return;
      }

      subjectSelect.disabled = true;
      subjectSelect.innerHTML = '<option value="">Loading subjects...</option>';

      try {
        const res = await fetch(`/admin/curriculum/hierarchy-filter/?level=subjects&grade_id=${gradeId}`);
        const data = await res.json();
        if (data.success) {
          populateSelect(subjectSelect, data.data, preserveSelected, '--- Select Subject ---', 'name');
          if (preserveSelected) {
            loadChapters(gradeId, preserveSelected, initialChapterId);
          } else {
            if (topicSelect) resetSelect(topicSelect, '--- Select Subject first ---');
            if (chapterSelect) resetSelect(chapterSelect, '--- Select Subject first ---');
            if (conceptSelect) resetSelect(conceptSelect, '--- Select Chapter first ---');
          }
        }
      } catch (err) {
        console.error('Error loading subjects:', err);
        resetSelect(subjectSelect, 'Error loading subjects');
      }
    }

    // Fetch chapters for grade + subject
    async function loadChapters(gradeId, subjectId, preserveSelected = null) {
      const targetSelect = topicSelect || chapterSelect;
      if (!targetSelect) return;

      if (!gradeId || !subjectId) {
        resetSelect(targetSelect, '--- Select Subject first ---');
        if (conceptSelect) resetSelect(conceptSelect, '--- Select Chapter first ---');
        return;
      }

      targetSelect.disabled = true;
      targetSelect.innerHTML = '<option value="">Loading chapters...</option>';

      try {
        const res = await fetch(`/admin/curriculum/hierarchy-filter/?level=chapters&grade_id=${gradeId}&subject_id=${subjectId}`);
        const data = await res.json();
        if (data.success) {
          populateSelect(targetSelect, data.data, preserveSelected, '--- Select Chapter ---', 'title');
          if (conceptSelect) {
            if (preserveSelected) {
              loadConcepts(preserveSelected, initialConceptId);
            } else {
              resetSelect(conceptSelect, '--- Select Chapter first ---');
            }
          }
        }
      } catch (err) {
        console.error('Error loading chapters:', err);
        resetSelect(targetSelect, 'Error loading chapters');
      }
    }

    // Fetch concepts for chapter (Game form only)
    async function loadConcepts(chapterId, preserveSelected = null) {
      if (!conceptSelect) return;
      if (!chapterId) {
        resetSelect(conceptSelect, '--- Select Chapter first ---');
        return;
      }

      conceptSelect.disabled = true;
      conceptSelect.innerHTML = '<option value="">Loading concepts...</option>';

      try {
        const res = await fetch(`/admin/curriculum/hierarchy-filter/?level=concepts&chapter_id=${chapterId}`);
        const data = await res.json();
        if (data.success) {
          populateSelect(conceptSelect, data.data, preserveSelected, '--- Select Concept ---', 'title');
        }
      } catch (err) {
        console.error('Error loading concepts:', err);
        resetSelect(conceptSelect, 'Error loading concepts');
      }
    }

    // Event listeners for upstream changes
    gradeSelect.addEventListener('change', function() {
      loadSubjects(this.value, null);
    });

    if (subjectSelect) {
      subjectSelect.addEventListener('change', function() {
        loadChapters(gradeSelect.value, this.value, null);
      });
    }

    if (chapterSelect) {
      chapterSelect.addEventListener('change', function() {
        loadConcepts(this.value, null);
      });
    }

    // Initial setup on page load
    if (initialGradeId) {
      loadSubjects(initialGradeId, initialSubjectId);
    } else {
      if (subjectSelect) resetSelect(subjectSelect, '--- Select Grade first ---');
      if (topicSelect) resetSelect(topicSelect, '--- Select Subject first ---');
      if (chapterSelect) resetSelect(chapterSelect, '--- Select Subject first ---');
      if (conceptSelect) resetSelect(conceptSelect, '--- Select Chapter first ---');
    }
  });
})();
