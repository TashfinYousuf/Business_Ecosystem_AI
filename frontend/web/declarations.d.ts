/**
 * frontend/web/declarations.d.ts
 * Global module declarations for static assets and CSS side-effect imports.
 */

declare module "*.css" {
  const content: { [className: string]: string };
  export default content;
}