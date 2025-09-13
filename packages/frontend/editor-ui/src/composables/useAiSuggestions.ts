import axios from 'axios'
import { useWorkflowsStore } from '@/stores/workflows.store'
import { useCanvasOperations } from './useCanvasOperations'

export function useAiSuggestions() {
  const workflowsStore = useWorkflowsStore()
  const canvasOperations = useCanvasOperations()

  async function requestSuggestions() {
    const { data } = await axios.post('/rest/ai/suggestions', { workflow: workflowsStore.workflow.value })
    for (const action of data.actions ?? []) {
      if (action.type === 'addNode' && action.node) {
        await canvasOperations.addNodes([action.node], {})
      } else if (action.type === 'updateParameter' && action.node && action.parameter) {
        workflowsStore.setNodeValue({ name: action.node, key: `parameters.${action.parameter}`, value: action.value })
      }
    }
  }

  return { requestSuggestions }
}
