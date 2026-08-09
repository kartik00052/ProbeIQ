import { createBrowserRouter } from 'react-router-dom'
import App from '../App'
import { ROUTES } from '../constants/routes'
import { RequireAuth } from '../components/auth/RequireAuth'
import LandingPage from '../pages/LandingPage/LandingPage'
import CandidateSetup from '../pages/CandidateSetup/CandidateSetup'
import Interview from '../pages/Interview/Interview'
import Feedback from '../pages/Feedback/Feedback'
import Login from '../pages/Login/Login'
import Register from '../pages/Register/Register'

export const router = createBrowserRouter([
  {
    path: ROUTES.landing,
    element: <App />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: ROUTES.login, element: <Login /> },
      { path: ROUTES.register, element: <Register /> },
      {
        path: ROUTES.setup,
        element: (
          <RequireAuth>
            <CandidateSetup />
          </RequireAuth>
        ),
      },
      {
        path: ROUTES.interview,
        element: (
          <RequireAuth>
            <Interview />
          </RequireAuth>
        ),
      },
      {
        path: ROUTES.complete,
        element: (
          <RequireAuth>
            <Feedback />
          </RequireAuth>
        ),
      },
    ],
  },
])
