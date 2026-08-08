import { createBrowserRouter } from 'react-router-dom'
import App from '../App'
import { ROUTES } from '../constants/routes'
import LandingPage from '../pages/LandingPage/LandingPage'
import CandidateSetup from '../pages/CandidateSetup/CandidateSetup'
import Interview from '../pages/Interview/Interview'
import Feedback from '../pages/Feedback/Feedback'

export const router = createBrowserRouter([
  {
    path: ROUTES.landing,
    element: <App />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: ROUTES.setup, element: <CandidateSetup /> },
      { path: ROUTES.interview, element: <Interview /> },
      { path: ROUTES.complete, element: <Feedback /> },
    ],
  },
])
