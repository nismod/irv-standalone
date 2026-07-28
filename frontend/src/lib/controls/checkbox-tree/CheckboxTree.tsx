import { useCallback, ReactElement } from 'react';
import { SimpleTreeView } from '@mui/x-tree-view';

import { dfs, getDescendants, TreeNode } from './tree-node';
import { CheckboxTreeItem } from './CheckboxTreeItem';

export interface CheckboxTreeConfig<T> {
  roots: TreeNode<T>[];
  nodes: {
    [nodeId: string]: TreeNode<T> & {
      descendantIds: string[];
    };
  };
}

export function buildTreeConfig<T>(nodes: TreeNode<T>[]): CheckboxTreeConfig<T> {
  const config: CheckboxTreeConfig<T> = {
    roots: nodes,
    nodes: {},
  };

  nodes.forEach((node) => {
    dfs(node, (node) => {
      config.nodes[node.id] = {
        ...node,
        descendantIds: getDescendants(node),
      };
    });
  });
  return config;
}

export interface CheckboxTreeState {
  checked: { [nodeId: string]: boolean };
  indeterminate: { [nodeId: string]: boolean };
}

export function recalculateCheckboxStates<T>(
  state: CheckboxTreeState,
  config: CheckboxTreeConfig<T>,
  disabledNodeIds = new Set<string>(),
): CheckboxTreeState {
  const nextState = {
    checked: { ...state.checked },
    indeterminate: { ...state.indeterminate },
  };

  disabledNodeIds.forEach((nodeId) => {
    nextState.checked[nodeId] = false;
    nextState.indeterminate[nodeId] = false;
  });

  for (const root of config.roots) {
    // traverse each root tree in post-order to recalculate state starting from leaf nodes
    dfs(
      root,
      (node) => {
        const nodeChildren = config.nodes[node.id].children;
        if (nodeChildren) {
          const enabledChildren = nodeChildren.filter((child) => !disabledNodeIds.has(child.id));
          const checked =
            enabledChildren.length > 0 && enabledChildren.every((child) => nextState.checked[child.id]);
          const indeterminate =
            !checked &&
            enabledChildren.some(
              (child) => nextState.checked[child.id] || nextState.indeterminate[child.id],
            );
          nextState.checked[node.id] = checked;
          nextState.indeterminate[node.id] = indeterminate;
        }
      },
      false,
      'post',
    );
  }

  return nextState;
}

export function CheckboxTree<T>({
  nodes,
  config,
  getLabel,
  checkboxState,
  onCheckboxState,
  expanded,
  onExpanded,
  disableCheck = false,
  disabledNodeIds = new Set<string>(),
}: {
  config: CheckboxTreeConfig<T>;
  nodes: TreeNode<T>[];
  getLabel: (node: TreeNode<T>, checked: boolean) => string | ReactElement;
  checkboxState: CheckboxTreeState;
  onCheckboxState: (state: CheckboxTreeState) => void;
  expanded: string[];
  onExpanded: (expanded: string[]) => void;
  disableCheck?: boolean;
  disabledNodeIds?: Set<string>;
}) {
  const handleChange = useCallback(
    (checked: boolean, node: TreeNode<T>) => {
      if (disabledNodeIds.has(node.id)) return;

      const descendants: string[] = config.nodes[node.id].descendantIds;
      const nextChecked = {
        ...checkboxState.checked,
        [node.id]: checked,
      };
      descendants
        .filter((nodeId) => !disabledNodeIds.has(nodeId))
        .forEach((nodeId) => (nextChecked[nodeId] = checked));

      onCheckboxState(
        recalculateCheckboxStates(
          {
            checked: nextChecked,
            indeterminate: checkboxState.indeterminate,
          },
          config,
          disabledNodeIds,
        ),
      );
    },
    [checkboxState, config, disabledNodeIds, onCheckboxState],
  );

  return (
    <>
      <SimpleTreeView
        expandedItems={expanded}
        onExpandedItemsChange={(e, nodeIds) => onExpanded(nodeIds)}
        multiSelect
        selectedItems={Object.keys(checkboxState.checked).filter((id) => checkboxState.checked[id])}
      >
        {nodes.map((node) => (
          <CheckboxTreeItem
            key={node.id}
            root={node}
            checkboxState={checkboxState}
            handleChange={handleChange}
            getLabel={getLabel}
            disableCheck={disableCheck}
            disabledNodeIds={disabledNodeIds}
          />
        ))}
      </SimpleTreeView>
    </>
  );
}
