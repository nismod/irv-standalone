import { TreeItem } from '@mui/x-tree-view';
import { Box, Checkbox } from '@mui/material';
import { ReactElement } from 'react';

import { CheckboxTreeState } from './CheckboxTree';
import { TreeNode } from './tree-node';

function handleClick(e) {
  e.stopPropagation();
  return true;
}

export function CheckboxTreeItem<T>({
  root,
  handleChange,
  checkboxState,
  getLabel,
  disableCheck = false,
  disabledNodeIds = new Set<string>(),
}: {
  root: TreeNode<T>;
  handleChange: (checked: boolean, node: TreeNode<T>) => void;
  checkboxState: CheckboxTreeState;
  getLabel: (node: TreeNode<T>, checked: boolean) => string | ReactElement;
  disableCheck?: boolean;
  disabledNodeIds?: Set<string>;
}) {
  const indeterminate = Boolean(checkboxState.indeterminate[root.id]);
  const checked = indeterminate || Boolean(checkboxState.checked[root.id]);
  const disabled = disableCheck || disabledNodeIds.has(root.id);

  function handleCheckboxChange(event) {
    if (disabled) return;
    handleChange(event.currentTarget.checked, root);
  }

  function handleItemKeyDown(event) {
    if (disabled) return;
    if (event.key === 'Enter' || event.key === ' ') {
      handleChange(!checked, root);
      event.stopPropagation();
    }
  }

  const checkedState = indeterminate ? 'mixed' : checked ? 'true' : 'false';
  return (
    <TreeItem
      aria-checked={checkedState}
      key={root.id}
      itemId={root.id}
      onKeyDown={handleItemKeyDown}
      label={
        <Box display="flex" alignItems="center" width="100%">
          <Checkbox
            checked={checked}
            indeterminate={indeterminate}
            onChange={handleCheckboxChange}
            onClick={handleClick}
            disabled={disabled}
            slotProps={{
              input: {
                'aria-label': root.label,
              },
            }}
          />
          <Box flexGrow={1}>{getLabel(root, checked)}</Box>
        </Box>
      }
    >
      {root.children?.map((node) => (
        <CheckboxTreeItem
          key={node.id}
          root={node}
          handleChange={handleChange}
          checkboxState={checkboxState}
          getLabel={getLabel}
          disableCheck={disableCheck}
          disabledNodeIds={disabledNodeIds}
        ></CheckboxTreeItem>
      ))}
    </TreeItem>
  );
}
