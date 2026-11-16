import { useAtomValue, useSetAtom } from 'jotai';
import { ModelParameterControls } from 'lib/model-scenarios/ModelParameterControls';
import { modelParametersState } from 'lib/model-scenarios/state';
import { protectedFeatureScenarioState } from 'lib/state/protected-features';

export function ProtectedScenarioControls() {
  const { catalog, parameters } = useAtomValue(protectedFeatureScenarioState);
  const setParameters = useSetAtom(modelParametersState('adaptation'));
  return (
    <ModelParameterControls
      rows={catalog?.rows}
      parameters={parameters}
      onChange={setParameters}
      error={catalog?.error}
    />
  );
}
