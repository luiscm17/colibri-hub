# PR3 Runtime Evidence: Warehouse Bale 403 Recovery

## Bounded Live Checkpoint

- Existing local services returned HTTP 200 before the attempt; no service was started, stopped, reset, or provisioned.
- A pre-existing active local fixture was used. A temporary registration of the backend-defined `warehouse.raw_materials` scope and its exact `read`/`write` grants was created only to exercise the Warehouse reception flow, then removed after the check.
- The browser authenticated, entered the Warehouse Bale reception destination, and retained a valid one-bale draft while the backend grant changed.
- The pre-submit snapshot was allowed by the current backend Access response.
- The temporary `write + warehouse.raw_materials` permission was removed immediately before confirmation. The mutation request returned HTTP 403.
- Exactly one subsequent `GET /api/v1/access/me` returned HTTP 200. No second `POST /api/v1/warehouse/bales` occurred.
- The UI displayed the Access Denied route state and the notification: "Tu acceso cambió. Se conservaron los datos ingresados." The safe reception draft remained in React state until route reevaluation replaced the protected surface.

## Request Counts

| Request | Count | Status |
|---|---:|---|
| `POST /api/v1/warehouse/bales` | 1 | 403 |
| `GET /api/v1/access/me` after the 403 | 1 | 200 |
| Automatic replay of the mutation | 0 | N/A |

## Cleanup

- Removed the temporary Warehouse scope and its temporary role permissions.
- No Bale batch or Bale record was persisted because the only mutation returned 403.
- Restored the fixture user's authorization-version value to its pre-check value.
- Closed the Playwright browser session. No credentials or tokens were saved.
- No persistent synthetic fixture was retained, so `backend/http/CREDENTIALS.md` required no change.

## Scope Boundary

This runtime proof covers the implemented Warehouse Bale protected operation only. The branch has no Yarn, Quality/Waste, Lot-stage, or Transversal operation adapters; their PR2 catalog requirements remain exact but do not constitute runnable PR3 operation surfaces.

## Maintainer Scope Decision

The maintainer explicitly closed PR3 against its current applicable scope: scalable reusable exact action/scope contracts and shared 403 recovery must serve present and future capability owners, but Access Control must not invent absent owner-domain operations. Therefore, the existing Warehouse Bale read/write integration and runtime checkpoint satisfy this slice. No Bale edit/edit-outside-window operation or Yarn, Quality/Waste, Lot-stage, or Transversal operation was implemented or claimed.
