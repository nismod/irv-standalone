import { MapLibreOverlay, MapLibreOverlayProps } from '@deck.gl/maplibre';
import { forwardRef, useImperativeHandle } from 'react';
import { useControl } from 'react-map-gl/maplibre';

type DeckGLOverlayProps = MapLibreOverlayProps;

const DeckGLOverlayWithRef = (props, ref) => {
  const overlay = useControl(() => new MapLibreOverlay(props));
  overlay.setProps(props);

  useImperativeHandle(ref, () => overlay);

  return null;
};
export const DeckGLOverlay = forwardRef<MapLibreOverlay, DeckGLOverlayProps>(DeckGLOverlayWithRef);
