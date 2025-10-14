const React = require('react');

let navigateMock = jest.fn();
let locationMock = {
  pathname: '/',
  search: '',
  hash: '',
  state: null,
  key: 'mock'
};

const BrowserRouter = ({ children }) => <div data-testid="mock-browser-router">{children}</div>;
const MemoryRouter = ({ children }) => <div data-testid="mock-memory-router">{children}</div>;
const Routes = ({ children }) => <>{children}</>;
const Route = ({ element }) => element ?? null;

const Link = ({ to, children, ...rest }) => (
  <a href={typeof to === 'string' ? to : '#'} {...rest}>
    {children}
  </a>
);

const Outlet = ({ children }) => children ?? null;

const Navigate = ({ to }) => (
  <div data-testid="mock-navigate">{`Navigate to ${typeof to === 'string' ? to : JSON.stringify(to)}`}</div>
);

const useNavigate = () => navigateMock;
const useLocation = () => locationMock;
const useParams = () => ({
  /* no-op params mock */
});
const useRouteError = () => undefined;

const __setNavigateMock = (fn) => {
  navigateMock = typeof fn === 'function' ? fn : jest.fn();
};

const __setLocationMock = (nextLocation) => {
  locationMock = {
    pathname: '/',
    search: '',
    hash: '',
    state: null,
    key: 'mock',
    ...(nextLocation || {})
  };
};

const __resetRouterMocks = () => {
  navigateMock = jest.fn();
  locationMock = {
    pathname: '/',
    search: '',
    hash: '',
    state: null,
    key: 'mock'
  };
};

module.exports = {
  __esModule: true,
  BrowserRouter,
  MemoryRouter,
  Routes,
  Route,
  Link,
  Outlet,
  Navigate,
  useNavigate,
  useLocation,
  useParams,
  useRouteError,
  __setNavigateMock,
  __setLocationMock,
  __resetRouterMocks
};
