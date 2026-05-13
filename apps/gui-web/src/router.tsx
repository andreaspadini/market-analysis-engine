import { RouterProvider } from "react-router-dom";
import { router } from "@project/gui";

export function GuiRouterProvider() {
  return <RouterProvider router={router} />;
}